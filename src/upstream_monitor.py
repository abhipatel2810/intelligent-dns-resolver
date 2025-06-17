import time
import dns.resolver
import json
import os
from collections import deque, defaultdict

# Upstream DNS servers to test
upstreams = {
    "Google": "8.8.8.8",
    "Cloudflare": "1.1.1.1",
    "Quad9": "9.9.9.9"
}

# Rolling success and RTT logs
history = defaultdict(lambda: deque(maxlen=20))  # Increased window for stability
output_file = "data/data.json"

def probe_upstream():
    result = {}
    for name, ip in upstreams.items():
        resolver = dns.resolver.Resolver()
        resolver.nameservers = [ip]
        resolver.timeout = 2
        resolver.lifetime = 4

        try:
            start = time.time()
            response = resolver.resolve("example.com", "A")
            rtt_ms = round((time.time() - start) * 1000, 2)

            ttl_values = [r.ttl for r in response.response.answer] if response.response.answer else [60]
            ttl_var = max(ttl_values) - min(ttl_values)

            history[name].append((1, rtt_ms))
            log_msg = f"[SUCCESS] {name} - RTT: {rtt_ms} ms, TTL Variability: {ttl_var}"
        except Exception as e:
            history[name].append((0, 1000))  # Log high RTT for failure
            ttl_var = 0
            log_msg = f"[FAILURE] {name} - Error: {str(e)}"

        past = list(history[name])
        success_rate = sum(1 for s, _ in past if s == 1) / len(past)
        valid_rtt = [r for s, r in past if s == 1]
        avg_rtt = round(sum(valid_rtt) / len(valid_rtt), 2) if valid_rtt else 1000

        result[name] = {
            "ip": ip,
            "avg_rtt": avg_rtt,
            "success_rate": round(success_rate, 2),
            "ttl_var": ttl_var
        }

        print(log_msg)

    # Save result to JSON
    os.makedirs("data", exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)

    print(f"[{time.strftime('%H:%M:%S')}] Probed upstreams and updated {output_file}")

if __name__ == "__main__":
    print("Starting upstream monitoring...")
    while True:
        probe_upstream()
        time.sleep(30)
