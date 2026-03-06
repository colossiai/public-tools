# Grafana container monitor mysql container

1. setup containers

```bash
# bind all address, expose to host port 3307
docker run --name mysql84 -p 3307:3306 -e MYSQL_BIND_ADDRESS=0.0.0.0 -e MYSQL_ROOT_PASSWORD=123456 --restart unless-stopped -d mysql:8.4.4

docker run --name mac-grafana -d -p 3000:3000 -e GF_SECURITY_ADMIN_USER=admin -e GF_SECURITY_ADMIN_PASSWORD=123 grafana/grafana

```


2. setup common network


```bash

docker network create monitor-hub
docker network connect monitor-hub mac-grafana
docker network connect monitor-hub mysql84

# test network
docker exec -it mac-grafana bash # ping mysql84 is OK!

```

3. Add datasource for mysql

Use DSN: mysql84:`3306`, not mysql84:3307, `mac-grafana` connect with same network `monitor-hub`, no need port mapping!!