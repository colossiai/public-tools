# ==============================
# MySQL DevOps Toolkit
# ==============================

DB_HOST ?= localhost
DB_PORT ?= 3306
DB_NAME ?= testdb
DB_USER ?= "$(MYSQL_USER)"
DB_PASS ?= "$(MYSQL_PASS)"

MYSQL_URI := $(DB_USER):$(DB_PASS)@$(DB_HOST):$(DB_PORT)/$(DB_NAME)

define mysql_js
mysqlsh --js --uri="$(MYSQL_URI)" -e "$(1)"
endef

.DEFAULT_GOAL := help

.PHONY: help

help: ## Show this help message
	@echo ""
	@echo "MySQL DevOps Toolkit"
	@echo "===================="
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z0-9_-]+:.*?##/ {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""

# ------------------------
# Open interactive shell
# ------------------------
db-shell: ## Open interactive mysqlsh shell
	@mysqlsh --uri="$(MYSQL_URI)"

# ------------------------
# Run SQL query
# ------------------------
db-query: ## Run SQL query (usage: make db-query SQL="SELECT * FROM users")
	@$(call mysql_js,\
	var r=session.runSql('$(SQL)').fetchAll(); \
	print(JSON.stringify(r,null,2));)

# ------------------------
# DB health check
# ------------------------
db-health: ## Check database health
	@$(call mysql_js,\
	var r=session.runSql('SELECT NOW(), VERSION()').fetchOne(); \
	print(JSON.stringify({time:r[0],version:r[1]}));)

# ------------------------
# Count rows
# ------------------------
db-count: ## Count rows (usage: make db-count TABLE=users)
	@$(call mysql_js,\
	var r=session.runSql('SELECT COUNT(*) FROM $(TABLE)').fetchOne(); \
	print(JSON.stringify({table:'$(TABLE)',count:r[0]}));)

# ------------------------
# List tables
# ------------------------
db-tables: ## List database tables
	@$(call mysql_js,\
	var rows=session.runSql('SHOW TABLES').fetchAll(); \
	print(JSON.stringify(rows,null,2));)

# ------------------------
# Database size
# ------------------------
db-size: ## Show database size
	@$(call mysql_js,\
	var r=session.runSql(`SELECT \
	table_schema, \
	ROUND(SUM(data_length+index_length)/1024/1024,2) AS MB \
	FROM information_schema.tables \
	WHERE table_schema='$(DB_NAME)' \
	GROUP BY table_schema`).fetchAll(); \
	print(JSON.stringify(r,null,2));)

# ------------------------
# Largest tables
# ------------------------
db-top-tables: ## Show largest tables
	@$(call mysql_js,\
	var r=session.runSql(`SELECT \
	table_name, \
	ROUND((data_length+index_length)/1024/1024,2) AS MB \
	FROM information_schema.tables \
	WHERE table_schema='$(DB_NAME)' \
	ORDER BY MB DESC LIMIT 10`).fetchAll(); \
	print(JSON.stringify(r,null,2));)

# ------------------------
# Slow queries
# ------------------------
db-slow-queries: ## Show slow queries (performance_schema required)
	@$(call mysql_js,\
	var r=session.runSql(`SELECT \
	digest_text, \
	count_star, \
	round(sum_timer_wait/1000000000000,3) total_sec \
	FROM performance_schema.events_statements_summary_by_digest \
	ORDER BY sum_timer_wait DESC \
	LIMIT 10`).fetchAll(); \
	print(JSON.stringify(r,null,2));)

# ------------------------
# Run migration
# ------------------------
db-migrate: ## Run SQL migration (usage: make db-migrate FILE=sql/init.sql)
	mysqlsh --sql --uri="$(MYSQL_URI)" -f $(FILE)

# ------------------------
# Backup database
# ------------------------
db-backup: ## Backup database
	mysqldump -h $(DB_HOST) -P $(DB_PORT) -u $(DB_USER) -p$(DB_PASS) $(DB_NAME) > backup_$(DB_NAME)_$$(date +%Y%m%d_%H%M%S).sql