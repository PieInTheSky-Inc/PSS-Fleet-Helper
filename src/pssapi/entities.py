from datetime import datetime as _datetime
from typing import Any as _Any
from typing import Dict as _Dict
from typing import List as _List
from typing import Optional as _Optional

from . import convert as _convert
from . import enums as _enums
from . import utils as _utils


class PssEntityBase():
    pass


class PssAllianceRaw(PssEntityBase):
    def __init__(self, alliance_info: _Dict[str, _Any]) -> None:
        self.__alliance_info: _Dict[str, _Any] = dict(alliance_info)
        self.__members: _List['PssUserRaw'] = None
        self.__members_updated: _datetime = None


    @property
    def championship_score(self) -> _Optional[int]:
        return _convert.str_to_int(self.__alliance_info.get('ChampionshipScore'))

    @property
    def description(self) -> _Optional[str]:
        return self.__alliance_info.get('AllianceDescription')

    @property
    def division_design_id(self) -> _Optional[int]:
        return _convert.str_to_int(self.__alliance_info.get('DivisionDesignId'))

    @property
    def id(self) -> _Optional[int]:
        return _convert.str_to_int(self.__alliance_info.get('AllianceId'))

    @property
    def members(self) -> _Optional[_List['PssUserRaw']]:
        return self.__members

    @property
    def members_updated(self) -> _Optional[_datetime]:
        return self.__members_updated

    @property
    def name(self) -> _Optional[str]:
        return self.__alliance_info.get('AllianceName')

    @property
    def score(self) -> _Optional[int]:
        return _convert.str_to_int(self.__alliance_info.get('Score'))

    @property
    def sprite_id(self) -> _Optional[int]:
        return _convert.str_to_int(self.__alliance_info.get('SpriteId'))

    @property
    def trophy(self) -> _Optional[int]:
        return _convert.str_to_int(self.__alliance_info.get('Trophy'))


    async def fetch_members(self, access_token: str) -> _List['PssUserRaw']:
        from . import alliance_service as _alliance_service
        members: _List['PssUserRaw'] = await _alliance_service.list_users(self.id, access_token)
        self.__members_updated = _utils.get_utc_now()
        self.__members = members
        for member in members:
            if member.alliance_id == self.id:
                member.set_alliance(self)
        return members





class PssAlliance(PssAllianceRaw):
    def __init__(self, alliance_info: _Dict[str, _Any]):
        super().__init__(alliance_info)


    @property
    def members(self) -> _Optional[_List['PssUser']]:
        return self.__members


    async def fetch_members(self, access_token: str) -> _List['PssUser']:
        from . import alliance_service as _alliance_service
        members: _List['PssUserRaw'] = await _alliance_service.list_users(self.id, access_token)
        super().__members_updated = _utils.get_utc_now()
        super().__members = [PssUser(member.user_info) for member in members]
        for member in members:
            if member.alliance_id == self.id:
                member.set_alliance(self)
        return members





class PssUserRaw(PssEntityBase):
    def __init__(self, user_info: _Dict[str, _Any]) -> None:
        self.__user_info: _Dict[str, _Any] = dict(user_info)


    @property
    def alliance_id(self) -> _Optional[int]:
        return _convert.str_to_int(self.__user_info.get('AllianceId'))

    @property
    def alliance_info(self) -> _Dict[str, _Any]:
        return self.__user_info.get('Alliance')

    @property
    def alliance_join_date(self) -> _Optional[_datetime]:
        return _convert.str_to_datetime(self.__user_info.get('AllianceJoinDate'))

    @property
    def alliance_membership(self) -> _Optional[_enums.AllianceMembership]:
        return _convert.str_to_enum(self.__user_info.get('AllianceMembership'), _enums.AllianceMembership)

    @property
    def alliance_score(self) -> _Optional[int]:
        return _convert.str_to_int(self.__user_info.get('AllianceScore'))

    @property
    def championship_score(self) -> _Optional[int]:
        return _convert.str_to_int(self.__user_info.get('ChampionshipScore'))

    @property
    def creation_date(self) -> _Optional[_datetime]:
        return _convert.str_to_datetime(self.__user_info.get('CreationDate'))

    @property
    def crew_donated(self) -> _Optional[int]:
        return _convert.str_to_int(self.__user_info.get('CrewDonated'))

    @property
    def crew_received(self) -> _Optional[int]:
        return _convert.str_to_int(self.__user_info.get('CrewReceived'))

    @property
    def fleet_rank(self) -> _Optional[_enums.AllianceMembership]:
        return self.alliance_membership

    @property
    def highest_trophy(self) -> _Optional[int]:
        return _convert.str_to_int(self.__user_info.get('HighestTrophy'))

    @property
    def icon_sprite_id(self) -> _Optional[int]:
        return _convert.str_to_int(self.__user_info.get('IconSpriteId'))

    @property
    def id(self) -> _Optional[int]:
        return _convert.str_to_int(self.__user_info.get('Id'))

    @property
    def last_login_date(self) -> _Optional[_datetime]:
        return _convert.str_to_datetime(self.__user_info.get('LastLoginDate'))

    @property
    def name(self) -> _Optional[str]:
        return self.__user_info.get('Name')

    @property
    def pvp_attack_draws(self) -> _Optional[int]:
        return _convert.str_to_int(self.__user_info.get('PVPAttackDraws'))

    @property
    def pvp_attack_losses(self) -> _Optional[int]:
        return _convert.str_to_int(self.__user_info.get('PVPAttackLosses'))

    @property
    def pvp_attack_wins(self) -> _Optional[int]:
        return _convert.str_to_int(self.__user_info.get('PVPAttackWins'))

    @property
    def pvp_defence_draws(self) -> _Optional[int]:
        return _convert.str_to_int(self.__user_info.get('PVPDefenceDraws'))

    @property
    def pvp_defence_losses(self) -> _Optional[int]:
        return _convert.str_to_int(self.__user_info.get('PVPDefenceLosses'))

    @property
    def pvp_defence_wins(self) -> _Optional[int]:
        return _convert.str_to_int(self.__user_info.get('PVPDefenceWins'))

    @property
    def stars(self) -> _Optional[int]:
        return self.alliance_score

    @property
    def trophies(self) -> _Optional[int]:
        return self.trophy

    @property
    def trophy(self) -> _Optional[int]:
        return _convert.str_to_int(self.__user_info.get('Trophy'))

    @property
    def user_info(self) -> _Dict[str, _Any]:
        return self.__user_info


    def set_alliance(self, alliance: 'PssAllianceRaw') -> None:
        self.__user_info['Alliance'] = alliance
        self.__user_info['AllianceId'] = alliance.id





class PssUser(PssUserRaw):
    def __init__(self, user_info: _Dict[str, _Any]):
        super().__init__(user_info)
        if 'Alliance' in self.__user_info.keys():
            self.set_alliance(PssAlliance(alliance_info))


    @property
    def alliance(self) -> 'PssAlliance':
        return self.__user_info['Alliance']


    def set_alliance(self, alliance: 'PssAlliance') -> None:
        self.__user_info['Alliance'] = alliance
        self.__user_info['AllianceId'] = alliance.id