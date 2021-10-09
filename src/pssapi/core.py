import aiohttp as _aiohttp
from typing import Dict as _Dict

from . import settings as _settings
from . import convert as _convert
from .types import EntityInfo as _EntityInfo



# ---------- Constants ----------

__LATEST_SETTINGS_BASE_PATH: str = 'SettingService/GetLatestVersion3'
__LATEST_SETTINGS_BASE_PARAMS: _Dict = {
    'deviceType': _settings.DEVICE_TYPE,
    'languageKey': _settings.LANGUAGE_KEY,
}





# ---------- Functions ----------

async def get_base_url() -> str:
    production_server = await __get_production_server()
    result = f'https://{production_server}/'
    return result


async def get_data_from_path(path: str, **params) -> str:
    if path:
        path = path.strip('/')
    base_url = await get_base_url()
    url = f'{base_url}{path}'
    return await __get_data_from_url(url, **params)


async def get_latest_settings(base_url: str = None) -> _EntityInfo:
    base_url = base_url or await get_base_url()
    url = f'{base_url}{__LATEST_SETTINGS_BASE_PATH}'
    raw_text = await __get_data_from_url(url, **__LATEST_SETTINGS_BASE_PARAMS)
    result = _convert.xmltree_to_dict3(raw_text)
    maintenance_message = result.get('MaintenanceMessage')
    if maintenance_message:
        raise Exception(maintenance_message)
    return result


async def __get_data_from_url(url: str, **params) -> str:
    async with _aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            data = await response.text(encoding='utf-8')
    return data


async def __get_production_server() -> str:
    if _settings.OVERWRITE_PSS_PRODUCTION_SERVER:
        return _settings.OVERWRITE_PSS_PRODUCTION_SERVER
    latest_settings = await get_latest_settings(base_url=_settings.DEFAULT_PSS_PRODUCTION_SERVER)
    return latest_settings['ProductionServer']