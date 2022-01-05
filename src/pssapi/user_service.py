import aiohttp as _aiohttp
import hashlib as _hashlib
from typing import Dict as _Dict
from typing import Optional as _Optional

from . import convert as _convert
from . import core as _core
from . import utils as _pss_utils
from . import settings as _settings


# ---------- Constants ----------

__LOGIN_BASE_PATH: str = 'UserService/DeviceLogin11'
__LOGIN_BASE_PARAMS: _Dict[str, str] = {
    'deviceKey': _settings.DEVICE_ID,
    'deviceType': _settings.DEVICE_TYPE,
    'isJailBroken': 'false',
    'languageKey': 'en',
    'advertisingKey': '""',
}





# ---------- Functions ----------

async def device_login() -> _Optional[str]:
    client_datetime = _pss_utils.format_pss_timestamp(_pss_utils.get_utc_now())
    base_url = await _core.get_base_url()
    url = f'{base_url}{__LOGIN_BASE_PATH}'
    params = dict(__LOGIN_BASE_PARAMS)
    params['clientDateTime'] = client_datetime
    if 'checksum' not in params:
        params['checksum'] = __create_device_checksum(_settings.DEVICE_ID, _settings.DEVICE_TYPE, client_datetime)

    async with _aiohttp.ClientSession() as session:
        async with session.post(url, params=params) as response:
            data = await response.text(encoding='utf-8')

    login_info = _convert.raw_xml_to_dict(data)
    if 'UserService' in login_info.keys():
        result = login_info['UserService']['UserLogin']['accessToken']
    else:
        raise Exception(login_info.get('errorMessage', 'An error ocurred while logging in.'))
    return result


def __create_device_checksum(device_key: str, device_type: str, client_datetime: str) -> str:
    result = _hashlib.md5((f'{device_key}{client_datetime}{device_type}{_settings.PSS_DEVICE_LOGIN_CHECKSUM_KEY}savysoda').encode('utf-8')).hexdigest()
    return result