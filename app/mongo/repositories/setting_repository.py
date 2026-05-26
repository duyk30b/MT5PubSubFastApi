from app.mongo.models.setting_model import (
    SettingCreateSchema,
    SettingFilterSchema,
    SettingModel,
    SettingSortSchema,
    SettingUpdateSchema,
)
from app.mongo.mongo_repository import MongoRepository


class SettingRepository(
    MongoRepository[
        SettingModel,
        SettingCreateSchema,
        SettingUpdateSchema,
        SettingFilterSchema,
        SettingSortSchema,
    ]
):
    def __init__(self):
        super().__init__(SettingModel)


setting_repository = SettingRepository()
