from app.postgres.entities.setting_entity import (
    SettingCreateDict,
    SettingEntity,
    SettingFilterDict,
    SettingSortDict,
    SettingUpdateDict,
)
from app.postgres.postgres_repository import PostgresRepository


class SettingRepository(
    PostgresRepository[
        SettingEntity,
        SettingCreateDict,
        SettingUpdateDict,
        SettingFilterDict,
        SettingSortDict,
    ]
):
    def __init__(self):
        super().__init__(SettingEntity)


setting_repository = SettingRepository()
