# Makefile for managing Docker Compose services

# Variables
COMPOSE_FILE = docker-compose.yml

# Start services
start:
	docker compose -f $(COMPOSE_FILE) up -d

# Stop services
stop:
	docker compose -f $(COMPOSE_FILE) down

# View logs
logs:
	docker compose -f $(COMPOSE_FILE) logs -f

# Restart services
restart:
	docker compose -f $(COMPOSE_FILE) restart

# Clean up (stops services and removes containers)
clean:
	docker compose -f $(COMPOSE_FILE) down --volumes --remove-orphans

# Status of running containers
status:
	docker ps --filter "name=redis" --filter "name=redis_exporter" --filter "name=prometheus" --filter "name=grafana"

.PHONY: start stop logs restart clean status
