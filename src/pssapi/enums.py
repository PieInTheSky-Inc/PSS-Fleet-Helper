from enum import IntEnum as _IntEnum
from typing import Optional as _Optional
from typing import Type as _Type

from strenum import StrEnum as _StrEnum


# ---------- Enumerations ----------

class AllianceMembership(_IntEnum):
    FleetAdmiral = 0
    ViceAdmiral = 1
    Commander = 2
    Major = 3
    Lieutenant = 4
    Ensign = 5
    Candidate = 6


class ActivityType(_StrEnum):
    None_ = 'None'
    Replay = 'Replay'
    Application = 'Application'
    Joined = 'Joined'
    MembershipChanged = 'MembershipChanged'
    Invited = 'Invited'
    Donated = 'Donated'
    Reward = 'Reward'
    RewardCollected = 'RewardCollected'
    DeviceLogin = 'DeviceLogin'
    MarketListed = 'MarketListed'
    MarketSold = 'MarketSold'
    MarketExpired = 'MarketExpired'
    RewardPending = 'RewardPending'
    Unfriended = 'Unfriended'
    BattleMatched = 'BattleMatched'
    BattleLoadProgress = 'BattleLoadProgress'
    AllianceSettingsUpdated = 'AllianceSettingsUpdated'
    AllianceQualified = 'AllianceQualified'
    Actioned = 'Actioned'
    ModelUpdate = 'ModelUpdate'
    FriendRequestDecline = 'FriendRequestDecline'
    FriendRequestAccept = 'FriendRequestAccept'


class MessageType(_StrEnum):
    Public = 'Public'
    Private = 'Private'
    System = 'System'
    Alliance = 'Alliance'
    Moments = 'Moments'
    Market = 'Market'
    Catalog = 'Catalog'
    Battle = 'Battle'
    Tournament = 'Tournament'
    Mission = 'Mission'
    Task = 'Task'
    Global = 'Global'





# ---------- Helper ----------

def from_str(value: str, enum: _Type[_StrEnum]) -> _Optional[_Type[_StrEnum]]:
    if not value:
        return None
    for enum_value in enum:
        if value == enum_value.value:
            return enum_value.name
    raise TypeError(f'{enum} does not have a member with value: {value}')