import json

from fastapi import Query
from pydantic import BaseModel, Field

from app.postgres.entities.mt5_account_entity import MT5AccountType


class Mt5AccountFilter(BaseModel):
    accountLogin: int | None = Field(default=None)


class Mt5AccountSort(BaseModel):
    id: int | None = Field(default=None)  # 1: asc, -1: desc


class Mt5AccountRelation(BaseModel):
    pass


class Mt5AccountQuery(BaseModel):
    filter: Mt5AccountFilter = Field(default_factory=Mt5AccountFilter)
    sort: Mt5AccountSort = Field(default_factory=Mt5AccountSort)
    relation: Mt5AccountRelation = Field(default_factory=Mt5AccountRelation)

    @staticmethod
    def load_query(
        filter: str = Query("{}"),
        sort: str = Query("{}"),
        relation: str = Query("{}"),
    ) -> "Mt5AccountQuery":
        return Mt5AccountQuery(
            filter=Mt5AccountFilter(**json.loads(filter)),
            sort=Mt5AccountSort(**json.loads(sort)),
            relation=Mt5AccountRelation(**json.loads(relation)),
        )


class Mt5AccountCreateInfo(BaseModel):
    accountType: MT5AccountType = Field(...)
    accountLogin: int = Field(...)
    accountName: str = Field(...)
    accountServer: str = Field(...)
    accountPassword: str = Field(...)
    copyMultiplier: float = Field(...)
    copyMasterLogin: int = Field(...)
    description: str = Field(...)


class Mt5AccountUpdateInfo(BaseModel):
    accountType: MT5AccountType = Field(...)
    accountLogin: int = Field(...)
    accountName: str = Field(...)
    accountServer: str = Field(...)
    accountPassword: str = Field(...)
    copyMultiplier: float = Field(...)
    copyMasterLogin: int = Field(...)
    description: str = Field(...)


class Mt5AccountCreateBody(BaseModel):
    mt5Account: Mt5AccountCreateInfo = Field(...)
    programName: str = Field(...)


class Mt5AccountUpdateBody(BaseModel):
    mt5Account: Mt5AccountUpdateInfo = Field(...)
    programName: str = Field(...)
