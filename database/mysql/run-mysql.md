# Run mysql container

* container name=testdb
* persistent data in `/home/xxx/docker_data/mysql`
* root pass = xxx
* exposed port = 3307
* mysql version = 9.4

```bash
docker run --name testdb -v /home/xxx/docker_data/mysql:/var/lib/mysql -e MYSQL_ROOT_PASSWORD=xxx -p 3307:3306 -d mysql:9.4
```
