from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.api_mt5_program.mt5_program_service import MT5ProgramService
from app.depends.request_depends import RequestDepends, RequestState
from app.postgres.postgres_connection import PostgresConnection

mt5_program_controller = APIRouter(prefix="/mt5_program", tags=["MT5 Program"])
mt5_program_service = MT5ProgramService()


@mt5_program_controller.post("/refresh_all")
async def refresh_all(
    state: RequestState = Depends(RequestDepends.state),
    db: AsyncSession = Depends(PostgresConnection.get_db),
):
    return await mt5_program_service.refresh_all(db=db)


@mt5_program_controller.post("/open_all")
async def open_all(
    state: RequestState = Depends(RequestDepends.state),
    db: AsyncSession = Depends(PostgresConnection.get_db),
):
    return await mt5_program_service.open_all(db=db)


@mt5_program_controller.post("/close_all")
async def close_all(
    state: RequestState = Depends(RequestDepends.state),
    db: AsyncSession = Depends(PostgresConnection.get_db),
):
    return await mt5_program_service.close_all(db=db)


@mt5_program_controller.post("/refresh/{program_name}")
async def refresh(
    program_name: str,
    state: RequestState = Depends(RequestDepends.state),
    db: AsyncSession = Depends(PostgresConnection.get_db),
):
    return await mt5_program_service.refresh(db=db, program_name=program_name)


@mt5_program_controller.post("/open/{program_name}")
async def open(
    program_name: str,
    state: RequestState = Depends(RequestDepends.state),
    db: AsyncSession = Depends(PostgresConnection.get_db),
):
    return await mt5_program_service.open(db=db, program_name=program_name)


@mt5_program_controller.post("/close/{program_name}")
async def close(
    program_name: str,
    state: RequestState = Depends(RequestDepends.state),
    db: AsyncSession = Depends(PostgresConnection.get_db),
):
    return await mt5_program_service.close(db=db, program_name=program_name)


@mt5_program_controller.post("/copy_enabled/{program_name}")
async def copy_enabled(
    program_name: str,
    state: RequestState = Depends(RequestDepends.state),
    db: AsyncSession = Depends(PostgresConnection.get_db),
):
    return await mt5_program_service.copy_enabled(db=db, program_name=program_name)


@mt5_program_controller.post("/copy_disabled/{program_name}")
async def copy_disabled(
    program_name: str,
    state: RequestState = Depends(RequestDepends.state),
    db: AsyncSession = Depends(PostgresConnection.get_db),
):
    return await mt5_program_service.copy_disabled(db=db, program_name=program_name)


@mt5_program_controller.post("/setting/{program_name}")
async def setting(
    program_name: str,
    state: RequestState = Depends(RequestDepends.state),
    db: AsyncSession = Depends(PostgresConnection.get_db),
):
    return await mt5_program_service.setting(db=db, program_name=program_name)


@mt5_program_controller.post("/clear_log/{program_name}")
async def clear_log(
    program_name: str,
    state: RequestState = Depends(RequestDepends.state),
):
    return await mt5_program_service.clear_log(program_name=program_name)


@mt5_program_controller.post("/clear_error/{program_name}")
async def clear_error(
    program_name: str,
    state: RequestState = Depends(RequestDepends.state),
):
    return await mt5_program_service.clear_error(program_name=program_name)
