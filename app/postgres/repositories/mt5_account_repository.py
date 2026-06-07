from app.postgres.entities.mt5_account_entity import (
    MT5AccountCreateDict,
    MT5AccountEntity,
    MT5AccountFilterDict,
    MT5AccountSortDict,
    MT5AccountUpdateDict,
)
from app.postgres.postgres_repository import PostgresRepository


class MT5AccountRepository(
    PostgresRepository[
        MT5AccountEntity,
        MT5AccountCreateDict,
        MT5AccountUpdateDict,
        MT5AccountFilterDict,
        MT5AccountSortDict,
    ]
):
    def __init__(self):
        super().__init__(MT5AccountEntity)


mt5_account_repository = MT5AccountRepository()
