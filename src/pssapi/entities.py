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




class PssMessage(PssEntityBase):
    def __init__(self, message_info: _Dict[str, _Any]) -> None:
        self.__message_id: int = _convert.str_to_int(message_info.get('MessageId'))
        self.__activity_argument: str = message_info.get('ActivityArgument')
        self.__activity_type: _enums.ActivityType = _enums.from_str(message_info.get('ActivityType'))
        self.__alliance_id: int = _convert.str_to_int(message_info.get('AllianceId'))
        self.__alliance_name: str = message_info.get('AllianceName')
        self.__argument: str = message_info.get('Argument')
        self.__border_sprite_id: int = _convert.str_to_int(message_info.get('BorderSpriteId'))
        self.__channel_id: int = _convert.str_to_int(message_info.get('ChannelId'))
        self.__message: str = message_info.get('Message')
        self.__message_date: _datetime = _convert.str_to_datetime(message_info.get('MessageDate'))
        self.__message_type: _enums.MessageType = _enums.from_str(message_info.get('MessageType'))
        self.__ship_design_id: int = _convert.str_to_int(message_info.get('ShipDesignId'))
        self.__trophy: int = _convert.str_to_int(message_info.get('Trophy'))
        self.__user_id: int = _convert.str_to_int(message_info.get('UserId'))
        self.__user_name: str = message_info.get('UserName')
        self.__user_sprite_id: int = _convert.str_to_int(message_info.get('UserSpriteId'))


    @property
    def activity_argument(self) -> int:
        return self.__activity_argument

    @property
    def activity_type(self) -> _enums.ActivityType:
        return self.__activity_type

    @property
    def alliance_id(self) -> int:
        return self.__alliance_id

    @property
    def alliance_name(self) -> str:
        return self.__alliance_name

    @property
    def argument(self) -> str:
        return self.__argument

    @property
    def border_sprite_id(self) -> int:
        return self.__border_sprite_id

    @property
    def channel_id(self) -> int:
        return self.__channel_id

    @property
    def message(self) -> str:
        return self.__message

    @property
    def message_date(self) -> _datetime:
        return self.__message_date

    @property
    def message_id(self) -> int:
        return self.__message_id

    @property
    def message_type(self) -> _enums.MessageType:
        return self.__message_type

    @property
    def ship_design_id(self) -> int:
        return self.__ship_design_id

    @property
    def trophy(self) -> int:
        return self.__trophy

    @property
    def user_id(self) -> int:
        return self.__user_id

    @property
    def user_name(self) -> str:
        return self.__user_name

    @property
    def user_sprite_id(self) -> int:
        return self.__user_sprite_id





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