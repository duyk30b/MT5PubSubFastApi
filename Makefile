dev:
	uv run uvicorn app.main:socket_app --host 0.0.0.0 --reload

prod:
	uv run uvicorn app.main:socket_app --host 0.0.0.0 --port 8000 --workers 1

type:
	uv run pyright app
	uv run mypy app

build:
	uv run python -m compileall app

check: type build

dev-old:
	uv run fastapi dev app/main.py --host 0.0.0.0 

up: 
	docker compose up -d --build

logs: 
	docker compose logs -f api_public | cut -d '|' -f2-

clear-postgres:	
	@echo "=== Dropping and recreating database mea_sql... ==="
	docker compose exec mps_postgres sh -c '\
		psql -U mea -d postgres -c "DROP DATABASE IF EXISTS mea_sql;"; \
		psql -U mea -d postgres -c "CREATE DATABASE mea_sql;"; \
	'

restore-postgres:
	@echo "=== Restoring database from SQL file... ==="
	docker compose exec mps_postgres sh -c '\
		ls -la /restore; \
		psql "dbname=mea_sql user=mea password=Abc12345" < /restore/$$(ls -1 /restore | head -n 1); \
	'
	@echo "=== Restore database from SQL file successfully !!! ==="

production-up:
	mkdir -p ./data/backup
	mkdir -p ./data/postgres
	mkdir -p ./data/restore
	docker compose up -d --build

production-upgrade:
	git fetch --all --prune
	git log --all --oneline --graph -10
	git reset --hard origin/master
	docker compose up -d --build --force-recreate api_public
	docker compose logs -f api_public

production-logs:
	docker compose logs -f api_public

production-reload-nginx:
	git fetch --all --prune
	git log --all --oneline --graph -10
	git reset --hard origin/master
	docker compose restart mps_nginx
	docker compose exec mps_nginx nginx -t
	docker compose exec mps_nginx nginx -s reload

production-backup-postgres: 
	git fetch --all --prune
	git reset --hard origin/master
	git log --all --oneline --graph -10
	docker compose exec mps_postgres sh -c '\
		pg_dump "dbname=mea_sql user=mea password=Abc12345" > /backup/$$(date +%Y-%m-%d_%H-%M-%S).sql; \
		ls -la /backup; \
	'
	git status
	git add .
	git commit -m "backup-postgres"
	git push origin master

production-restore-postgres:
	docker compose exec mps_postgres sh -c '\
		ls -la /restore; \
		psql "dbname=mea_sql user=mea password=Abc12345" < /restore/$$(ls -1 /restore); \
	'

backup-mariadb: 
	docker compose -f docker.db.yml exec mariadb sh -c '\
		mkdir -p backup; \
		chmod -R 777 /backup; \
		mariadb-dump --user=mea --password=Abc12345 --lock-tables --all-databases > /backup/$$(date +%Y-%m-%d_%H-%M-%S).sql; \
		ls -la /backup; \
	'

restore-mariadb:
	docker compose -f docker.db.yml exec mariadb sh -c '\
		ls -la /restore; \
		mariadb --user=mea --password=Abc12345 mea_sql < /restore/$$(ls -1 /restore); \
	'
		