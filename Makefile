dev:
	.venv\Scripts\python.exe -m uvicorn app.main:socket_app --host 0.0.0.0 --port 8000 --reload --env-file .env.dev

prod:
	.venv\Scripts\python.exe -m uvicorn app.main:socket_app --host 0.0.0.0 --port 8000 --workers 1 --env-file .env.prod

alembic-dev:
	.venv\Scripts\alembic.exe -x env_file=.env.dev $(ARGS)

alembic-prod:
	.venv\Scripts\alembic.exe -x env_file=.env.prod $(ARGS)

migration-dev:
	.venv\Scripts\alembic.exe -x env_file=.env.dev upgrade head

migration-prod:
	.venv\Scripts\alembic.exe -x env_file=.env.prod upgrade head

type:
	uv run pyright app
	uv run mypy app

build:
	uv run python -m compileall app

check: type build

production-upgrade:
	git fetch --all --prune
	git log --all --oneline --graph -10
	git reset --hard origin/main

