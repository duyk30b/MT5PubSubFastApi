import logging
from typing import Any

from sqlalchemy.orm import Session

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
        db: Session,
    ) -> dict[str, Any]:
        accounts = mt5_account_repository.find_many(db)
        mt5AccountList = [u.to_response() for u in accounts]
        return {"mt5AccountList": mt5AccountList}

    async def mt5_account_get_one(
        self, db: Session, query: Mt5AccountQuery
    ) -> dict[str, Any]:
        account = mt5_account_repository.find_one(
            db, filter={"accountLogin": query.filter.accountLogin}
        )
        if not account:
            return {"mt5Account": None}
        return {"mt5Account": account.to_response()}

    async def mt5_account_create(
        self,
        db: Session,
        body: Mt5AccountCreateBody,
    ) -> dict[str, Any]:
        existed = mt5_account_repository.find_one(
            db, {"accountLogin": body.mt5Account.accountLogin}
        )
        if existed:
            raise BusinessException("AccountLogin already exists")

        mt5Account = mt5_account_repository.insert_one(
            db,
            MT5AccountCreateDict(
                accountType=body.mt5Account.accountType,
                accountLogin=body.mt5Account.accountLogin,
                accountName=body.mt5Account.accountName,
                accountServer=body.mt5Account.accountServer,
                accountPassword=body.mt5Account.accountPassword,
                copyMultiplier=body.mt5Account.copyMultiplier,
                copyMasterLogin=body.mt5Account.copyMasterLogin,
                description=body.mt5Account.description,
            ),
        )

        mt5AccountResponse = mt5Account.to_response()

        await MT5ProgramCache.login_list_add(mt5AccountResponse["accountLogin"])

        await MT5ProgramCache.account_setting_set_mt5_account(
            mt5Account.accountLogin,
            mt5AccountResponse,
        )
        await MT5ProgramCache.account_setting_set_program_name(
            mt5Account.accountLogin,
            body.programName,
        )
        return {"mt5Account": mt5AccountResponse}

    async def mt5_account_update(
        self,
        db: Session,
        user_id: int,
        body: Mt5AccountUpdateBody,
    ) -> dict[str, Any]:

        mt5Account = mt5_account_repository.update_one_by_id(
            db,
            user_id,
            {
                "accountType": body.mt5Account.accountType,
                "accountLogin": body.mt5Account.accountLogin,
                "accountName": body.mt5Account.accountName,
                "accountServer": body.mt5Account.accountServer,
                "accountPassword": body.mt5Account.accountPassword,
                "copyMultiplier": body.mt5Account.copyMultiplier,
                "copyMasterLogin": body.mt5Account.copyMasterLogin,
                "description": body.mt5Account.description,
            },
        )
        if not mt5Account:
            raise BusinessException("User not found")

        mt5AccountResponse = mt5Account.to_response()

        await MT5ProgramCache.login_list_add(mt5AccountResponse["accountLogin"])

        await MT5ProgramCache.account_setting_set_mt5_account(
            mt5Account.accountLogin,
            mt5AccountResponse,
        )
        await MT5ProgramCache.account_setting_set_program_name(
            mt5Account.accountLogin,
            body.programName,
        )
        return {"mt5Account": mt5AccountResponse}
