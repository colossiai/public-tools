# add docker network if not exists: docker network create monitoring
docker run -d --name grafana --network monitoring -p 3000:3000 grafana/grafana 