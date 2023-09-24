from typing import Iterable as _Iterable
from typing import List as _List
from typing import Optional as _Optional
from typing import Tuple as _Tuple

from discord import Member as _Member
from discord import TextChannel as _TextChannel
from discord.ext.commands import Context as _Context
import sqlalchemy as _db
import pssapi as _pssapi

from . import orm as _orm
from .. import utils as _utils




class Fleet(_orm.ModelBase):
    ID_COLUMN_NAME: str = 'alliance_id'
    TABLE_NAME: str = 'fleet'
    __tablename__ = TABLE_NAME

    id = _db.Column(ID_COLUMN_NAME, _db.Integer, primary_key=True, nullable=False)
    guild_id = _db.Column('guild_id', _db.Integer, nullable=False)
    short_name = _db.Column('short_name', _db.Text, nullable=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__fleet: _pssapi.entities.Alliance = None
    
    @property
    def fleet(self) -> _pssapi.entities.Alliance:
        return self.__fleet
    
    async def get_fleet(self, pss_api_client: _pssapi.PssApiClient, access_token: str) -> _pssapi.entities.Alliance:
        self.__fleet = pss_api_client.alliance_service.get_alliance(access_token, self.id)
        return self.__fleet
    
    @classmethod
    def get_fleet_search_description(cls, alliance: _pssapi.entities.Alliance) -> str:
        return f'{alliance.alliance_name} (ID: {alliance.id}, rank {alliance.ranking} at {alliance.trophy} 🏆)'
    
    @classmethod
    def make(cls,
             alliance_id: int,
             guild_id: int,
             short_name: str = None,
    ) -> 'Fleet':
        result = Fleet(
            id=alliance_id,
            guild_id=guild_id,
            short_name=short_name or None,
            )
        return result