import math as _math
from typing import Optional as _Optional

import discord as _discord
import discord.ext.commands as _commands
import pssapi as _pssapi
from .. import bot_settings as _bot_settings
from . import settings as _settings
from .. import utils as _utils


class PssApiDiscordBot(_commands.Bot):
    def __init__(self, *args, device_type: _pssapi.enums.DeviceType = None, language_key: _pssapi.enums.LanguageKey = None, production_server: str = None, **kwargs):
        super().__init__(
            command_prefix=_commands.when_mentioned_or(*_bot_settings.DEFAULT_PREFIXES),
            intents=_discord.Intents.all(),
            activity=_discord.activity.Activity(type=_discord.ActivityType.playing, name='fh help'),
            *args,
            **kwargs
        )
        self.__pssapi_client: _pssapi.PssApiClient = _pssapi.PssApiClient(
            device_type=device_type,
            language_key=language_key,
            production_server=production_server
        )
    
    @property
    def pssapi_client(self) -> _pssapi.PssApiClient:
        return self.__pssapi_client
    
    async def pssapi_login(self) -> _Optional[str]:
        utc_now = _pssapi.utils.get_utc_now()
        if _settings.DEVICE_IDS:
            device_count = len(_settings.DEVICE_IDS)
            device_index = _math.floor(utc_now.hour / (24 / device_count))
            device_id = _settings.DEVICE_IDS[device_index]
        elif _settings.DEVICE_ID:
            device_id = _settings.DEVICE_ID
        checksum = self.pssapi_client.user_service.utils.create_device_login_checksum(device_id, self.pssapi_client.device_type, utc_now, _settings.PSS_DEVICE_LOGIN_CHECKSUM_KEY)
        user_login = await self.pssapi_client.user_service.device_login_11(checksum, utc_now, device_id, self.pssapi_client.device_type, self.pssapi_client.language_key)

        return user_login.access_token
        