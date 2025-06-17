import os
import time
import json
import joblib
import dns.message, dns.query
from flask import Flask, request, jsonify
from prometheus_client import start_http_server, Counter, Histogram
from collections import defaultdict

# Paths
BASE_DIR  = os.path.dirname(os.path.dirname(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models")
UPSTREAM_METRICS_FILE = os.path.join(BASE_DIR, "data", "data.json")

# Load ML model and encoders
model   = joblib.load(os.path.join(MODEL_DIR, "ml_model.joblib"))
le_type = joblib.load(os.path.join(MODEL_DIR, "le_query_type.joblib"))
le_up   = joblib.load(os.path.join(MODEL_DIR, "le_best_upstream.joblib"))

# Upstream Mapping
UPSTREAMS = {
    "Google":     "8.8.8.8",
    "Cloudflare": "1.1.1.1",
    "Quad9":      "9.9.9.9"
}

# Cache Storage
cache = defaultdict(lambda: None)

# Prometheus Metrics
Q_TOTAL   = Counter("dns_queries_total", "Total DNS queries received", ["type"])
CACHE_HIT = Counter("dns_cache_hits_total", "Total DNS cache hits", ["type"])
UP_HIT    = Counter("dns_upstream_selection_total", "Total upstream selections", ["upstream"])
ERRORS    = Counter("dns_resolver_errors_total", "Total DNS resolver errors")
RRT       = Histogram("dns_upstream_rtt_seconds", "DNS upstream response times (s)", ["upstream"], buckets=[0.01, 0.05, 0.1, 0.2, 0.5, 1, 2])

# Flask Setup
app = Flask(__name__)
start_http_server(9091)

def get_time_bucket():
    return time.localtime().tm_hour // 6

def load_metrics():
    try:
        with open(UPSTREAM_METRICS_FILE) as f:
            metrics = json.load(f)
        valid = [m for m in metrics.values() if m['avg_rtt'] > 0]
        if not valid:
            raise ValueError("No valid metrics found")
        return valid
    except Exception as e:
        print(f"[WARN] Using fallback metrics due to: {e}")
        return [{
            'avg_rtt': 50.0,
            'success_rate': 0.9,
            'ttl_var': 5.0
        }]

def predict_best(qtype, qlen):
    try:
        metrics = load_metrics()
        avg_rtt = sum(m['avg_rtt'] for m in metrics) / len(metrics)
        avg_success = sum(m['success_rate'] for m in metrics) / len(metrics)
        avg_ttl_var = sum(m['ttl_var'] for m in metrics) / len(metrics)

        qt_encoded = le_type.transform([qtype])[0]
        features = [[qt_encoded, qlen, get_time_bucket(), avg_rtt, avg_success, avg_ttl_var]]
        pred = model.predict(features)[0]
        probs = model.predict_proba(features)[0]
        confidence = max(probs)

        return le_up.inverse_transform([pred])[0], confidence
    except Exception as e:
        print(f"[WARN] Prediction fallback to Google due to: {e}")
        return "Google", 1.0

def check_cache(domain, qtype):
    key = f"{domain}_{qtype}"
    entry = cache.get(key)
    if entry and time.time() - entry[0] < entry[1]:
        return entry[2]
    if entry:
        del cache[key]
    return None

def forward_query(domain, qtype, upstream_ip, upstream_name):
    start = time.time()
    try:
        query = dns.message.make_query(domain, qtype)
        response = dns.query.udp(query, upstream_ip, timeout=2)
        RRT.labels(upstream=upstream_name).observe(time.time() - start)
        return response
    except Exception as e:
        print(f"[ERROR] Query failed: {e}")
        ERRORS.inc()
        return None

def cache_response(domain, qtype, answers, base_ttl, confidence):
    ttl = int(base_ttl * (0.5 if confidence < 0.7 else 1.0))
    cache[f"{domain}_{qtype}"] = (time.time(), ttl, answers)

@app.route('/resolve')
def resolve():
    domain = request.args.get('domain')
    qtype  = request.args.get('type', 'A')
    if not domain:
        return jsonify({"error": "Missing domain parameter"}), 400

    cached = check_cache(domain, qtype)
    if cached:
        CACHE_HIT.labels(type=qtype).inc()
        return jsonify({"domain": domain, "type": qtype, "upstream": "CACHE", "answers": cached})

    upstream, confidence = predict_best(qtype, len(domain))
    ip = UPSTREAMS.get(upstream, UPSTREAMS["Google"])

    Q_TOTAL.labels(type=qtype).inc()
    UP_HIT.labels(upstream=upstream).inc()

    response = forward_query(domain, qtype, ip, upstream)
    if not response or not response.answer:
        return jsonify({"error": "No DNS answer"}), 502

    answers = [item.to_text() for ans in response.answer for item in ans.items]
    base_ttl = min(ans.ttl for ans in response.answer)

    cache_response(domain, qtype, answers, base_ttl, confidence)

    return jsonify({"domain": domain, "type": qtype, "upstream": upstream, "answers": answers})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8053)
