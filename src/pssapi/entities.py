from typing import Optional as _Optional

from . import enums as _enums
from .raw_entities import EntityInfo as _EntityInfo
from .raw_entities import PssAllianceRaw as _PssAllianceRaw
from .raw_entities import PssMessageRaw as _PssMessageRaw
from .raw_entities import PssUserRaw as _PssUserRaw
from .raw_entities import PssEntityBase as _PssEntityBase


class PssAlliance(_PssEntityBase, _PssAllianceRaw):
    @property
    def id(self) -> int:
        """
        Alias for property `alliance_id`
        """
        return self.alliance_id


class PssMessage(_PssEntityBase, _PssMessageRaw):
    @property
    def id(self) -> int:
        """
        Alias for property `message_id`
        """
        return self.message_id


class PssUser(_PssUserRaw, _PssEntityBase):
    def __init__(self, user_info: _EntityInfo) -> None:
        super().__init__(user_info)


    @property
    def fleet_rank(self) -> _Optional[_enums.AllianceMembership]:
        """
        Alias for property `alliance_membership`
        """
        return self.alliance_membership

    @property
    def stars(self) -> _Optional[int]:
        """
        Alias for property `alliance_score`
        """
        return self.alliance_score

    @property
    def trophies(self) -> int:
        """
        Alias for property `trophy`
        """
        return self.trophy

    @property
    def user_id(self) -> int:
        """
        Alias for property `id`
        """
        return self.id