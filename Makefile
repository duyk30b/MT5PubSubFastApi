dev:
	uv run uvicorn app.main:socket_app --host 0.0.0.0 --reload

mt5-01:
	uv run python -m mt5.mt5_instance_01

mt5-02:
	uv run python -m mt5.mt5_instance_02

mt5-03:
	uv run python -m mt5.mt5_instance_03

mt5-04:
	uv run python -m mt5.mt5_instance_04

mt5-05:
	uv run python -m mt5.mt5_instance_05

mt5-all:
	cmd /C start "" /B uv run python -m mt5.mt5_instance_01
	cmd /C start "" /B uv run python -m mt5.mt5_instance_02
	cmd /C start "" /B uv run python -m mt5.mt5_instance_03
	cmd /C start "" /B uv run python -m mt5.mt5_instance_04
	cmd /C start "" /B uv run python -m mt5.mt5_instance_05

mt5-stop:
	powershell -NoProfile -Command "$$pattern = '-m\s+mt5\.mt5_instance_0[1-5](\s|$$)'; $$procs = Get-CimInstance Win32_Process | Where-Object { $$_.Name -match '^python(\.exe)?$$' -and $$_.CommandLine -match $$pattern }; if (-not $$procs) { Write-Host 'No MT5 instance process found.'; exit 0 }; foreach ($$p in $$procs) { Stop-Process -Id $$p.ProcessId -Force -ErrorAction SilentlyContinue; Write-Host ('Stopped PID=' + $$p.ProcessId) }"

mt5-status:
	powershell -NoProfile -Command "$$pattern = '-m\s+(mt5\.mt5_instance_0[1-5])(\s|$$)'; $$procs = Get-CimInstance Win32_Process | Where-Object { $$_.Name -match '^python(\.exe)?$$' -and $$_.CommandLine -match $$pattern }; if (-not $$procs) { Write-Host 'No MT5 instance process running.'; exit 0 }; $$rows = $$procs | ForEach-Object { if ($$_.CommandLine -match $$pattern) { [PSCustomObject]@{ Instance = $$Matches[1]; PID = $$_.ProcessId; CommandLine = $$_.CommandLine } } }; $$rows | Sort-Object Instance, PID | Format-Table -AutoSize"

mt5-task-install:
	powershell -NoProfile -ExecutionPolicy Bypass -File deploy/windows/install_mt5_tasks.ps1

mt5-task-start:
	powershell -NoProfile -ExecutionPolicy Bypass -File deploy/windows/start_mt5_tasks.ps1

mt5-task-stop:
	powershell -NoProfile -ExecutionPolicy Bypass -File deploy/windows/stop_mt5_tasks.ps1

mt5-task-status:
	powershell -NoProfile -ExecutionPolicy Bypass -File deploy/windows/status_mt5_tasks.ps1

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
	docker compose exec postgres_local sh -c '\
		psql -U mea -d postgres -c "DROP DATABASE IF EXISTS mea_sql;"; \
		psql -U mea -d postgres -c "CREATE DATABASE mea_sql;"; \
	'

restore-postgres:
	@echo "=== Restoring database from SQL file... ==="
	docker compose exec postgres_local sh -c '\
		ls -la /restore; \
		psql "dbname=mea_sql user=mea password=Abc12345" < /restore/$$(ls -1 /restore | head -n 1); \
	'
	@echo "=== Restore database from SQL file successfully !!! ==="

production-up:
	mkdir -p ./data/backup
	mkdir -p ./data/postgres
	mkdir -p ./data/restore
	docker compose -f docker-compose.production.yml up -d --build

production-upgrade:
	git fetch --all --prune
	git log --all --oneline --graph -10
	git reset --hard origin/master
	docker compose -f docker-compose.production.yml up -d --build --force-recreate api_public
	docker compose -f docker-compose.production.yml logs -f api_public

production-logs:
	docker compose logs -f api_public

production-reload-nginx:
	git fetch --all --prune
	git log --all --oneline --graph -10
	git reset --hard origin/master
	docker compose -f docker-compose.production.yml restart nginx
	docker compose -f docker-compose.production.yml exec nginx nginx -t
	docker compose -f docker-compose.production.yml exec nginx nginx -s reload

production-backup-postgres: 
	git fetch --all --prune
	git reset --hard origin/master
	git log --all --oneline --graph -10
	docker compose -f docker-compose.production.yml exec postgres sh -c '\
		pg_dump "dbname=mea_sql user=mea password=Abc12345" > /backup/$$(date +%Y-%m-%d_%H-%M-%S).sql; \
		ls -la /backup; \
	'
	git status
	git add .
	git commit -m "backup-postgres"
	git push origin master

production-restore-postgres:
	docker compose -f docker-compose.production.yml exec postgres sh -c '\
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
		