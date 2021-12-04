from typing import Dict as _Dict

import sqlalchemy as _db

from . import orm as _orm
from . import database as _database
from .. import utils as _utils


CONFIG: 'Config' = None


class BotSetting(_orm.ModelBase):
    ID_COLUMN_NAME: str = 'setting_name'
    TABLE_NAME: str = _database.TABLE_NAME_BOT_SETTINGS
    __tablename__ = TABLE_NAME


    id = _db.Column('setting_name', _db.Text, primary_key=True, nullable=False)
    name = id
    boolean = _db.Column('setting_boolean', _db.Boolean, nullable=True)
    float = _db.Column('setting_float', _db.Float, nullable=True)
    int = _db.Column('setting_int', _db.Integer, nullable=True)
    text = _db.Column('setting_text', _db.Text, nullable=True)
    timestamp = _db.Column('setting_timestamp', _db.DateTime, nullable=True)


class Config(object):
    def __init__(self) -> None:
        self.__bot_settings: _Dict[str, BotSetting] = {bot_setting.name: bot_setting for bot_setting in BotSetting.query.all()}
        if 'schema_version' not in self.__bot_settings.keys():
            raise Exception('Setting \'schema_version\' is not set!')


    @property
    def db_schema_version(self) -> str:
        return self.__bot_settings['schema_version'].text





# ---------- Initialization ----------

CONFIG = Config()