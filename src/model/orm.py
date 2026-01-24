from datetime import datetime as _datetime
from typing import List as _List
from typing import Generic as _Generic
from typing import Optional as _Optional
from typing import TypeVar as _TypeVar
from typing import Type as _Type

import sqlalchemy as _sqlalchemy
from sqlalchemy.ext.declarative import declarative_base as _declarative_base
from sqlalchemy.orm.query import Query as _Query
from sqlalchemy.orm.scoping import scoped_session as _scoped_session

from .database import DATABASE_URL


# ---------- Constants ----------

_ENGINE: _sqlalchemy.engine.Engine = _sqlalchemy.create_engine(DATABASE_URL)
_SESSION_MAKER: _sqlalchemy.orm.sessionmaker = _sqlalchemy.orm.sessionmaker(
    autocommit=False, autoflush=False, bind=_ENGINE
)
ScopedSession = _scoped_session


# ---------- Classes ----------

_Record = _declarative_base()

_T = _TypeVar("_T", bound="ModelBase")


class ModelBase(_Record, _Generic[_T]):
    CREATED_AT_COLUMN_NAME: str = "created_at"
    MODIFIED_AT_COLUMN_NAME: str = "modified_at"

    __abstract__ = True

    created_at = _sqlalchemy.Column(
        CREATED_AT_COLUMN_NAME, _sqlalchemy.DateTime, default=_datetime.utcnow
    )
    modified_at = _sqlalchemy.Column(
        MODIFIED_AT_COLUMN_NAME,
        _sqlalchemy.DateTime,
        default=_datetime.utcnow,
        onupdate=_datetime.utcnow,
    )

    def create(self, session: _scoped_session, commit: bool = True) -> _T:
        session.add(self)
        if commit:
            session.commit()
        return self

    def delete(self, session: _scoped_session, commit: bool = True) -> None:
        session.delete(self)
        if commit:
            session.commit()

    def reset_changes(self, session: _scoped_session) -> _T:
        session.rollback()
        return self

    def save(self, session: _scoped_session) -> _T:
        session.commit()
        return self


# ---------- Helper ----------


def create_session() -> _scoped_session:
    return _SESSION_MAKER(expire_on_commit=False)


def get_all(cls: _Type[_T], session: _scoped_session) -> _List[_T]:
    return get_query(cls, session).all()


def get_by_id(cls: _Type[_T], session: _scoped_session, id: int) -> _Optional[_T]:
    return get_query(cls, session).get(id)


def get_all_filtered_by(
    cls: _Type[_T], session: _scoped_session, **kwargs
) -> _List[_T]:
    return get_query(cls, session).filter_by(**kwargs).all()


def get_first_filtered_by(
    cls: _Type[_T], session: _scoped_session, **kwargs
) -> _Optional[_T]:
    return get_query(cls, session).filter_by(**kwargs).first()


def get_query(cls: _Type[_T], session: _scoped_session) -> _Query:
    return session.query(cls)


def merge(session: _scoped_session, instance: _T) -> _T:
    return session.merge(instance)
