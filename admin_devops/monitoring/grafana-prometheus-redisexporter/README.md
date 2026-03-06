# Monitor redis metrics in grafana

2025-JAN-16

* Access the Services
Redis: Runs on localhost:6379.
Redis Exporter: Metrics available on localhost:9121/metrics.
Prometheus: Access the UI at http://localhost:9090.
Grafana: Access the UI at http://localhost:3000 (default credentials: admin/admin).


* Set Up Redis Dashboard in Grafana
Log in to Grafana (http://localhost:3000).
Add Prometheus as a data source:
Navigate to Configuration > Data Sources.
Click Add data source and select Prometheus.
Set the URL to http://prometheus:9090 and save it.
Import the Redis Dashboard:
Go to Dashboards > Import.
Use a prebuilt dashboard ID like 763 from the Grafana Dashboard Repository.


* Monitor Redis Metrics
You should now see Redis metrics such as:

Total connections
Keyspace hits/misses
Memory usage
Connected clients
