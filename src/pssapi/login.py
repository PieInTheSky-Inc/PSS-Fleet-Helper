import aiohttp as _aiohttp
import hashlib as _hashlib
from typing import Dict as _Dict

from . import convert as _convert
from . import core as _core
from . import utils as _utils
from . import settings as _settings


# ---------- Constants ----------

__LOGIN_BASE_PATH: str = 'UserService/DeviceLogin8'
__LOGIN_BASE_PARAMS: _Dict[str, str] = {
    'deviceKey': _settings.DEVICE_ID,
    'deviceType': _settings.DEVICE_TYPE,
    'isJailBroken': 'false',
    'languageKey': 'en',
    'advertisingKey': '""',
}





# ---------- Functions ----------

async def login() -> str:
    base_url = await _core.get_base_url()
    url = f'{base_url}{__LOGIN_BASE_PATH}'
    if 'checksum' not in __LOGIN_BASE_PARAMS:
        __LOGIN_BASE_PARAMS['checksum'] = __create_device_checksum(_settings.DEVICE_ID, _settings.DEVICE_TYPE)

    async with _aiohttp.ClientSession() as session:
        async with session.post(url, params=__LOGIN_BASE_PARAMS) as response:
            data = await response.text(encoding='utf-8')

    login_info = _convert.raw_xml_to_dict(data)
    if 'UserService' in login_info.keys():
        result = login_info['UserService']['UserLogin']['accessToken']
    else:
        result = None
    return result


def __create_device_checksum(device_key: str, device_type: str) -> str:
    result = _hashlib.md5((f'{device_key}{device_type}savysoda').encode('utf-8')).hexdigest()
    return result