from abc import ABC as _ABC
from abc import abstractproperty as _abstractproperty
from datetime import datetime as _datetime
from typing import Any as _Any
from typing import Dict as _Dict
from typing import List as _List
from typing import Optional as _Optional
from typing import Union as _Union

from . import convert as _convert
from . import enums as _enums
from . import utils as _utils


EntityInfo = _Dict[str, _Union[str, 'EntityInfo']]


class PssEntityBase(_ABC):
    @_abstractproperty
    def id(self) -> int:
        raise NotImplemented()





class PssAllianceRaw():
    def __init__(self, alliance_info: EntityInfo):
        self.__alliance_id: int = _convert.str_to_int(alliance_info.get('AllianceId'))
        self.__alliance_name: str = alliance_info.get('AllianceName')
        self.__championship_score: int = _convert.str_to_int(alliance_info.get('ChampionshipScore'))
        self.__description: str = alliance_info.get('AllianceDescription')
        self.__division_design_id: int = _convert.str_to_int(alliance_info.get('DivisionDesignId'))
        self.__score: int = _convert.str_to_int(alliance_info.get('Score'))
        self.__sprite_id: int = _convert.str_to_int(alliance_info.get('SpriteId'))
        self.__trophy: int = _convert.str_to_int(alliance_info.get('Trophy'))


    @property
    def alliance_id(self) -> int:
        return self.__alliance_id

    @property
    def alliance_name(self) -> str:
        return self.__alliance_name

    @property
    def championship_score(self) -> int:
        return self.__championship_score

    @property
    def description(self) -> str:
        return self.__description

    @property
    def division_design_id(self) -> int:
        return self.__division_design_id

    @property
    def score(self) -> int:
        return self.__score

    @property
    def sprite_id(self) -> int:
        return self.__sprite_id

    @property
    def trophy(self) -> int:
        return self.__trophy




class PssMessageRaw():
    def __init__(self, message_info: EntityInfo) -> None:
        self.__message_id: int = _convert.str_to_int(message_info.get('MessageId'))
        self.__activity_argument: str = message_info.get('ActivityArgument')
        self.__activity_type: _enums.ActivityType = _enums.from_str(message_info.get('ActivityType'), _enums.ActivityType, raise_error=False)
        self.__alliance_id: int = _convert.str_to_int(message_info.get('AllianceId'))
        self.__alliance_name: str = message_info.get('AllianceName')
        self.__argument: str = message_info.get('Argument')
        self.__border_sprite_id: int = _convert.str_to_int(message_info.get('BorderSpriteId'))
        self.__channel_id: int = _convert.str_to_int(message_info.get('ChannelId'))
        self.__message: str = message_info.get('Message')
        self.__message_date: _datetime = _convert.str_to_datetime(message_info.get('MessageDate'))
        self.__message_type: _enums.MessageType = _enums.from_str(message_info.get('MessageType'), _enums.MessageType, raise_error=False)
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
    def fleet_name(self) -> str:
        return self.__alliance_name

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





class PssUserRaw():
    def __init__(self, user_info: EntityInfo) -> None:
        self.__alliance: _Optional[PssAllianceRaw] = PssAllianceRaw(user_info.get('Alliance', {}))
        self.__alliance_id: _Optional[int] = _convert.str_to_int(user_info.get('AllianceId'))
        self.__alliance_join_date: _Optional[_datetime] = _convert.str_to_datetime(user_info.get('AllianceJoinDate'))
        self.__alliance_membership: _Optional[_enums.AllianceMembership] = _convert.str_to_enum(user_info.get('AllianceMembership'), _enums.AllianceMembership)
        self.__alliance_score: _Optional[int] = _convert.str_to_int(user_info.get('AllianceScore'))
        self.__championship_score: int = _convert.str_to_int(user_info.get('ChampionshipScore'))
        self.__creation_date: _datetime = _convert.str_to_datetime(user_info.get('CreationDate'))
        self.__crew_donated: _Optional[int] = _convert.str_to_int(user_info.get('CrewDonated'))
        self.__crew_received: _Optional[int] = _convert.str_to_int(user_info.get('CrewReceived'))
        self.__highest_trophy: int = _convert.str_to_int(user_info.get('HighestTrophy'))
        self.__icon_sprite_id: int = _convert.str_to_int(user_info.get('IconSpriteId'))
        self.__id: int = _convert.str_to_int(user_info.get('Id'))
        self.__last_login_date: _datetime = _convert.str_to_datetime(user_info.get('LastLoginDate'))
        self.__name: str = user_info.get('Name')
        self.__pvp_attack_draws: int = _convert.str_to_int(user_info.get('PVPAttackDraws'))
        self.__pvp_attack_losses: int = _convert.str_to_int(user_info.get('PVPAttackLosses'))
        self.__pvp_attack_wins: int = _convert.str_to_int(user_info.get('PVPAttackWins'))
        self.__pvp_defence_draws: int = _convert.str_to_int(user_info.get('PVPDefenceDraws'))
        self.__pvp_defence_losses: int = _convert.str_to_int(user_info.get('PVPDefenceLosses'))
        self.__pvp_defence_wins: int = _convert.str_to_int(user_info.get('PVPDefenceWins'))
        self.__trophy: int = _convert.str_to_int(user_info.get('Trophy'))


    @property
    def alliance(self) -> _Optional[PssAllianceRaw]:
        return self.__alliance

    @property
    def alliance_id(self) -> _Optional[int]:
        return self.__alliance_id

    @property
    def alliance_join_date(self) -> _Optional[_datetime]:
        return self.__alliance_join_date

    @property
    def alliance_membership(self) -> _Optional[_enums.AllianceMembership]:
        return self.__alliance_membership

    @property
    def alliance_score(self) -> _Optional[int]:
        return self.__alliance_score

    @property
    def championship_score(self) -> int:
        return self.__championship_score

    @property
    def creation_date(self) -> _datetime:
        return self.__creation_date

    @property
    def crew_donated(self) -> _Optional[int]:
        return self.__crew_donated

    @property
    def crew_received(self) -> _Optional[int]:
        return self.__crew_received

    @property
    def highest_trophy(self) -> int:
        return self.__highest_trophy

    @property
    def icon_sprite_id(self) -> int:
        return self.__icon_sprite_id

    @property
    def id(self) -> int:
        return self.__id

    @property
    def last_login_date(self) -> _datetime:
        return self.__last_login_date

    @property
    def name(self) -> str:
        return self.__name

    @property
    def pvp_attack_draws(self) -> int:
        return self.__pvp_attack_draws

    @property
    def pvp_attack_losses(self) -> int:
        return self.__pvp_attack_losses

    @property
    def pvp_attack_wins(self) -> int:
        return self.__pvp_attack_wins

    @property
    def pvp_defence_draws(self) -> int:
        return self.__pvp_defence_draws

    @property
    def pvp_defence_losses(self) -> int:
        return self.__pvp_defence_losses

    @property
    def pvp_defence_wins(self) -> int:
        return self.__pvp_defence_wins

    @property
    def trophy(self) -> int:
        return self.__trophy