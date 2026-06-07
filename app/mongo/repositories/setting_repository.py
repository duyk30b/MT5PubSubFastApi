from app.mongo.models.setting_model import (
    SettingCreateDict,
    SettingFilterDict,
    SettingModel,
    SettingSortDict,
    SettingUpdateDict,
)
from app.mongo.mongo_repository import MongoRepository


class SettingRepository(
    MongoRepository[
        SettingModel,
        SettingCreateDict,
        SettingUpdateDict,
        SettingFilterDict,
        SettingSortDict,
    ]
):
    def __init__(self):
        super().__init__(SettingModel)


setting_repository = SettingRepository()
