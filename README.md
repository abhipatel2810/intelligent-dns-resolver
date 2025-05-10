---

# Intelligent DNS Resolver with Live Monitoring

An ML-powered DNS resolver with **Prometheus**, **Grafana**, and **Locust** for live monitoring and load testing.

---

## How to Run the Project

1. **Clone the Repository**

   ```bash
   git clone https://github.com/abhipatel2810/intelligent-dns-resolver.git
   cd intelligent-dns-resolver
   ```

2. **Start the Complete Stack**

   ```bash
   ./start.ps1
   ```

---

## Access URLs After Startup

* **Grafana Dashboard**: [http://localhost:3000](http://localhost:3000)
* **Prometheus Console**: [http://localhost:9090](http://localhost:9090)
  Example:

  ```
  http://localhost:8053/resolve?domain=example.com&type=A
  ```
* **Prometheus Metrics Endpoint**: [http://localhost:9091/metrics](http://localhost:9091/metrics)

---

## Running Locust Load Tests

1. **Run Locust with Command:**

   ```bash
   python -m locust -f locustfile.py --host=http://localhost:8053
   ```

2. **Access Locust Dashboard**:
   [http://localhost:8089](http://localhost:8089)

---

## Prometheus Query Examples

Visit [http://localhost:9090](http://localhost:9090) and run:

* **DNS Query Rate**

  ```promql
  rate(dns_queries_total[1m])
  ```

* **Cache Hit Rate**

  ```promql
  100 * sum(rate(dns_cache_hits_total[1m])) / sum(rate(dns_queries_total[1m]))
  ```

* **Upstream RTT Bucket**

  ```promql
  dns_upstream_rtt_seconds_bucket
  ```

* **DNS Errors**

  ```promql
  rate(dns_resolver_errors_total[1m])
  ```

###1. Query Rate Over Time : rate(dns_queries_total[1m])
###2. 95th percentile DNS round trip time:histogram_quantile(0.95, sum(rate(dns_upstream_rtt_seconds_bucket[5m])) by (le, upstream))
###3. Cache Hit Ratio:sum(rate(dns_cache_hits_total[5m])) / sum(rate(dns_queries_total[5m])) * 100
###4. Resolver Errors : rate(dns_resolver_errors_total[1m])




---

## Grafana Setup and Configuration

### Add Prometheus Data Source

1. Go to **[http://localhost:3000](http://localhost:3000)**.
2. **Login:**
   Default Username/Password: `admin / admin`
3. Navigate to:
   **⚙️  > Data Sources > Add Data Source > Prometheus**
4. Set URL to:

   ```
   http://host.docker.internal:9090
   ```
5. Click **Save & Test**.

### Example Grafana Query (Cache Hit %)

```promql
100 * (sum(rate(dns_cache_hits_total[1m]))) / (sum(rate(dns_queries_total[1m])))
```

#### Recommended Panel Settings:

* **Visualization**: Gauge or Stat
* **Unit**: Percent (0-100)
* **Thresholds**:

  * **Red**: < 50
  * **Yellow**: 50-80
  * **Green**: 80-100

---

## Troubleshooting

If **Grafana**, **Prometheus**, or **DNS Resolver** are not **UP**, rerun:

```bash
./start.ps1
```

Ensure:

* Docker Desktop is running.
* Ports **3000**, **8053**, **9090**, **9091**, and **8089** are free.

---

## All output text files and .txt files are there you can check that.

Enjoy the **Intelligent DNS Resolver with Real-Time Monitoring and Load Testing**.

---
