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
    fleet_name = _db.Column('fleet_name', _db.Text, nullable=False)
    short_name = _db.Column('short_name', _db.Text, nullable=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__alliance: _pssapi.entities.Alliance = None
    
    @property
    def alliance(self) -> _pssapi.entities.Alliance:
        return self.__alliance
    
    async def get_fleet(self, pss_api_client: _pssapi.PssApiClient, access_token: str) -> _pssapi.entities.Alliance:
        self.__alliance = await pss_api_client.alliance_service.get_alliance(access_token, self.id)
        return self.__alliance
    
    @classmethod
    def get_alliance_search_description(cls, alliance: _pssapi.entities.Alliance) -> str:
        return f'{alliance.alliance_name} (ID: {alliance.id}, rank {alliance.ranking} at {alliance.trophy} 🏆)'
    
    @classmethod
    def get_fleet_search_description(cls, fleet: 'Fleet') -> str:
        if fleet.short_name:
            return f'{fleet.alliance.alliance_name} [{fleet.short_name}] (ID: {fleet.alliance.id}, rank {fleet.alliance.ranking} at {fleet.alliance.trophy} 🏆)'
        return f'{fleet.alliance.alliance_name} (ID: {fleet.alliance.id}, rank {fleet.alliance.ranking} at {fleet.alliance.trophy} 🏆)'
    
    @classmethod
    def make(cls,
             alliance_id: int,
             guild_id: int,
             alliance_name: str,
             short_name: str = None,
    ) -> 'Fleet':
        result = Fleet(
            id=alliance_id,
            guild_id=guild_id,
            fleet_name=alliance_name,
            short_name=short_name or None,
            )
        return result