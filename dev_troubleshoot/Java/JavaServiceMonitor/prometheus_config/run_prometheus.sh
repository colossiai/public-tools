# Check Prometheus UI at `http://localhost:9090`.

# add docker network if not exists: docker network create monitoring
# -- name prometheus is crucial for grafana to connect to prometheus
docker run -d --network monitoring --name prometheus -p 9090:9090 -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml prom/prometheus
