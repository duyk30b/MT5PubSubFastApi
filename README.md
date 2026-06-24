# I. Install FastAPI
## VPS bị thiếu: Visual C++ Redistributable for Visual Studio 2015
- Donwload and Install: https://www.microsoft.com/en-us/download/details.aspx?id=48145
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

# II. Install Postgres
## 1. Setup
   `uv add alembic`
   `alembic init alembic`

## 2. Sửa ./alembic/env.py
```bash
from app.postgres.postgres_config import postgres_settings
from app.postgres.base_entity import Base

target_metadata = Base.metadata
config.set_main_option("sqlalchemy.url", postgres_settings.sqlalchemy_uri_migration)

from app.postgres.entities.user_entity import UserEntity  # noqa
```

## 3. Run migrate generate
- Generate
  `alembic revision --autogenerate -m "demo_version"`
  `make alembic-dev ARGS="revision --autogenerate -m 'demo_version'"`
- Get SQL
  `alembic upgrade head --sql`
- Run
  `alembic upgrade head`
- Rollback
  `alembic downgrade -1`


# III. Nginx
- Hướng dẫn lấy cert và key trên cloudflare
Website
 └─ SSL/TLS
      └─ Origin Server
      => Create Certificate

- Download and install: https://nginx.org/en/download.html

# IV. Startup with Windows
- Run: `C:\Projects\MT5PubSubFastApi\.venv\Scripts\python.exe -m uvicorn app.main:socket_app --host 0.0.0.0 --port 8000 --workers 1`
1. NSSM
- Download: https://nssm.cc/commands
- Copy file nssm on C:\Windows\system32> => Use CMD - Administrator
- VSCode: on project -> get python path:
`Get-Command python`
=> D:\Project\MT5PubSubFastApi\.venv/Scripts\python.exe
- Create service: 
`nssm version`
`nssm install FastAPI`
Path: D:\Project\MT5PubSubFastApi\.venv\Scripts\python.exe
Startup Directory: D:\Project\MT5PubSubFastApi
Arguments: -m uvicorn app.main:socket_app --host 0.0.0.0 --port 8000 --workers 1
==> Install service
- Sửa: `nssm edit FastAPI`
- Dừng: `nssm stop FastAPI`
- Xoá: `nssm remove FastAPI confirm`
- Ghi log
`nssm set FastAPI AppStdout D:\Project\MT5PubSubFastApi\logs\fastapi.log`
`nssm set FastAPI AppStderr D:\Project\MT5PubSubFastApi\logs\fastapi-error.log`

