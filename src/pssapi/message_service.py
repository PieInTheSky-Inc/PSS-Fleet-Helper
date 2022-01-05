from typing import List as _List

from . import convert as _convert
from . import core as _core
from .raw_entities import PssMessageRaw



# ---------- Constants ----------

__LIST_MESSAGES_FOR_CHANNEL_KEY_BASE_PATH: str = 'MessageService/ListMessagesForChannelKey'


# ---------- Functions ----------

async def list_messages_for_channel_key(channel_key: str, access_token: str) -> _List[PssMessageRaw]:
    params = {
        'accessToken': access_token,
        'channelKey': channel_key,
    }
    raw_xml = await _core.get_data_from_path(__LIST_MESSAGES_FOR_CHANNEL_KEY_BASE_PATH, **params)
    raw_dict = _convert.xmltree_to_dict3(raw_xml)
    result = [PssMessageRaw(d) for d in raw_dict.values()]
    return result