from datetime import datetime as _datetime

from flask import Flask as _Flask
from flask_sqlalchemy import SQLAlchemy as _SQLAlchemyBase
import sqlalchemy as _sqlalchemy
import flask_sqlalchemy as _flask_sqlalchemy

from . import model_settings as _model_settings
from .. import utils as _utils


DB: 'SQLAlchemy' = None


# ---------- Classes ----------

APP = _Flask('ViViBot')
APP.config['SQLALCHEMY_DATABASE_URI'] = _model_settings.DATABASE_URL

class SQLAlchemy(_SQLAlchemyBase):
    def apply_pool_defaults(self, app, options):
            options = super().apply_pool_defaults(app, options)

            if not options:
                options = {}

            options["pool_pre_ping"] = True
            return options


DB = SQLAlchemy(APP)


class DatabaseRowBase(DB.Model):
    CREATED_AT_COLUMN_NAME: str = 'created_at'
    MODIFIED_AT_COLUMN_NAME: str = 'modified_at'

    __abstract__ = True

    created_at = _sqlalchemy.Column(CREATED_AT_COLUMN_NAME, _sqlalchemy.DateTime, default=_datetime.utcnow)
    modified_at = _sqlalchemy.Column(MODIFIED_AT_COLUMN_NAME, _sqlalchemy.DateTime, default=_datetime.utcnow, onupdate=_datetime.utcnow)


    def create(self) -> None:
        DB.session.add(self)
        DB.session.commit()


    def save(self) -> None:
        DB.session.commit()


    def delete(self) -> None:
        DB.session.delete(self)
        DB.session.commit()