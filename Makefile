dev:
	.venv\Scripts\python.exe -m uvicorn app.main:socket_app --host 0.0.0.0 --port 8000 --reload --env-file .env.dev

prod:
	.venv\Scripts\python.exe -m uvicorn app.main:socket_app --host 0.0.0.0 --port 8000 --workers 1 --env-file .env.prod

type:
	uv run pyright app
	uv run mypy app

build:
	uv run python -m compileall app

check: type build

upgrade:
	git fetch --all --prune
	git log --all --oneline --graph -10
	git reset --hard origin/main
	.venv\Scripts\python.exe -m uvicorn app.main:socket_app --host 0.0.0.0 --port 8000 --workers 1 --env-file .env.prod

