from os import access
from typing import List as _List

from . import convert as _convert
from . import core as _core
from .entities import PssAllianceRaw as _PssAlliance
from .entities import PssUserRaw as _PssUser



# ---------- Constants ----------

__LIST_USERS_BASE_PATH: str = 'AllianceService/ListUsers'
__SEARCH_ALLIANCES_BASE_PATH: str = 'AllianceService/SearchAlliances'


# ---------- Functions ----------

async def search_alliances(name: str, access_token: str, skip: int = 0, take: int = 100) -> _List[_PssAlliance]:
    params = {
        'accessToken': access_token,
        'name': name,
        'skip': skip,
        'take': take,
    }
    raw_xml = await _core.get_data_from_path(__SEARCH_ALLIANCES_BASE_PATH, **params)
    raw_dict = _convert.xmltree_to_dict3(raw_xml)
    result = [_PssAlliance(d) for d in raw_dict.values()]
    return result


async def list_users(alliance_id: int, access_token: str, skip: int = 0, take: int = 100) -> _List[_PssUser]:
    params = {
        'accessToken': access_token,
        'allianceId': alliance_id,
        'skip': skip,
        'take': take,
    }
    raw_xml = await _core.get_data_from_path(__LIST_USERS_BASE_PATH, **params)
    raw_dict = _convert.xmltree_to_dict3(raw_xml)
    result = [_PssUser(d) for d in raw_dict.values()]
    return result