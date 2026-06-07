# I. Install Project
## 1. Install uv
   - 1.1. With Ubuntu: `curl -Ls https://astral.sh/uv/install.sh | sh`
   - 1.2. With MacOS: `brew install uv`
   - 1.3. With Window: Use PowerShell
     `irm https://astral.sh/uv/install.ps1 -OutFile install.ps1`
     `notepad install.ps1`
     `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`
     `.\install.ps1`
   - Restart VSCode
   - Check uv: `uv --version`

## 2. Init project fastapi with uv

- `uv init`
- `uv venv`
- `uv add "fastapi[standard]"`
- `uv pip list`
- `uv pip tree`
- `uv run uvicorn --version`
- `uv remove bcrypt`

## 3. Clone project

```bash
git clone ...
cd project
uv sync --reinstall --frozen
```

## 4. Run project
   `uv run fastapi dev`
   `uv run fastapi dev app/main.py`

## 5. Windows - Run auto activate
   `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`
   PowerShell: `.venv\Scripts\Activate.ps1`
   CMD: `.venv\Scripts\activate.bat`

# II. Migrate Database
## 1. Setup
   `uv add alembic`
   `alembic init alembic`

## 2. Sửa ./alembic/env.py
```bash
from app.postgres.postgres_config import postgres_settings
from app.postgres.base_entity import Base

target_metadata = Base.metadata
config.set_main_option(
    "sqlalchemy.url",
    postgres_settings.sqlalchemy_database_uri
)

from app.postgres.entities.user_entity import UserEntity  # noqa
```

## 3. Run migrate generate
- Generate
  `alembic revision --autogenerate -m "demo_version"`
- Get SQL
  `alembic upgrade head --sql`
- Run
  `alembic upgrade head`
- Rollback
  `alembic downgrade -1`

# III. Windows VPS - Manage 5 MT5 instance processes with Task Scheduler

- Files:
  - `deploy/windows/install_mt5_tasks.ps1`
  - `deploy/windows/start_mt5_tasks.ps1`
  - `deploy/windows/stop_mt5_tasks.ps1`
  - `deploy/windows/status_mt5_tasks.ps1`
- Open PowerShell as Administrator, then run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File deploy/windows/install_mt5_tasks.ps1
```

- Start all MT5 tasks:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File deploy/windows/start_mt5_tasks.ps1
```

- Stop all MT5 tasks:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File deploy/windows/stop_mt5_tasks.ps1
```

- Check task status:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File deploy/windows/status_mt5_tasks.ps1
```

- Shortcut via Makefile:
  - `make mt5-task-install`
  - `make mt5-task-start`
  - `make mt5-task-stop`
  - `make mt5-task-status`
