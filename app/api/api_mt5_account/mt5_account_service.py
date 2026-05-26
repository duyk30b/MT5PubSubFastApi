import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.api_mt5_account.mt5_account_request import (
    Mt5AccountCreateBody,
    Mt5AccountQuery,
    Mt5AccountUpdateBody,
)
from app.core.exception import BusinessException
from app.postgres.entities.mt5_account_entity import MT5AccountCreateDict
from app.postgres.repositories.mt5_account_repository import mt5_account_repository
from app.redis.cache.mt5_program_cache import MT5ProgramCache

logger = logging.getLogger(__name__)


class Mt5AccountService:
    def __init__(self):
        pass

    async def mt5_account_list(
        self,
        db: AsyncSession,
    ) -> dict[str, Any]:
        accounts = await mt5_account_repository.find_many(db)
        mt5AccountList = [u.to_response() for u in accounts]
        return {"mt5AccountList": mt5AccountList}

    async def mt5_account_get_one(
        self, db: AsyncSession, query: Mt5AccountQuery
    ) -> dict[str, Any]:
        account = await mt5_account_repository.find_one(
            db, filter={"accountLogin": query.filter.accountLogin}
        )
        if not account:
            return {"mt5Account": None}
        return {"mt5Account": account.to_response()}

    async def mt5_account_create(
        self,
        db: AsyncSession,
        body: Mt5AccountCreateBody,
    ) -> dict[str, Any]:
        existed = await mt5_account_repository.find_one(
            db, {"accountLogin": body.mt5Account.accountLogin}
        )
        if existed:
            raise BusinessException("AccountLogin already exists")

        mt5Account = await mt5_account_repository.insert_one(
            db,
            MT5AccountCreateDict(
                accountType=body.mt5Account.accountType,
                accountLogin=body.mt5Account.accountLogin,
                accountName=body.mt5Account.accountName,
                accountServer=body.mt5Account.accountServer,
                accountPassword=body.mt5Account.accountPassword,
                programName=body.mt5Account.programName,
                isOpening=body.mt5Account.isOpening,
                isCopying=body.mt5Account.isCopying,
                copyMultiplier=body.mt5Account.copyMultiplier,
                copyMasterLogin=body.mt5Account.copyMasterLogin,
                description=body.mt5Account.description,
            ),
        )

        mt5AccountResponse = mt5Account.to_response()
        await MT5ProgramCache.mt5_account_set_by_login_key(
            mt5Account.accountLogin,
            mt5AccountResponse,
        )
        return {"mt5Account": mt5AccountResponse}

    async def mt5_account_update(
        self,
        db: AsyncSession,
        mt5_account_id: int,
        body: Mt5AccountUpdateBody,
    ) -> dict[str, Any]:

        mt5Account = await mt5_account_repository.update_one_by_id(
            db,
            mt5_account_id,
            {
                "accountType": body.mt5Account.accountType,
                "copyMultiplier": body.mt5Account.copyMultiplier,
                "copyMasterLogin": body.mt5Account.copyMasterLogin,
                "description": body.mt5Account.description,
            },
        )
        if not mt5Account:
            raise BusinessException("MT5 account not found")

        mt5AccountResponse = mt5Account.to_response()
        await MT5ProgramCache.mt5_account_set_by_login_key(
            mt5Account.accountLogin,
            mt5AccountResponse,
        )
        return {"mt5Account": mt5AccountResponse}
