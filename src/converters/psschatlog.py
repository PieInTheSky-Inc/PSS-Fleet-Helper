from typing import List as _List

from discord import Guild as _Guild
from discord import TextChannel as _TextChannel
from discord.ext.commands import Bot as _Bot

from .. import utils as _utils
from ..model import PssChatLog as _PssChatLog



class PssChatLogConverter():
    def __init__(self, pss_chat_log: _PssChatLog) -> None:
        self.__pss_chat_log: _PssChatLog = pss_chat_log
        self.__text: _List[str] = None


    @property
    def pss_chat_log(self) -> _PssChatLog:
        return self.__pss_chat_log


    async def to_text(self, for_admin: bool, bot: _Bot = None) -> _List[str]:
        if self.__text is not None:
            return self.__text

        result = [
            f'**{self.pss_chat_log.name}** (ID: {self.pss_chat_log.id})',
            f'PSS Channel Key - {self.pss_chat_log.pss_channel_key}',
        ]
        if for_admin:
            guild: _Guild = bot.get_guild(self.pss_chat_log.guild_id)
            if guild:
                result.append(f'Guild - {guild.name} (ID: {self.pss_chat_log.guild_id})')
                channel: _TextChannel = guild.get_channel(self.pss_chat_log.channel_id)
                if channel:
                    result.append(f'Channel - {channel.name} (ID: {self.pss_chat_log.channel_id})')
                else:
                    result.append(f'Channel - Error: cannot access channel (ID: {self.pss_chat_log.channel_id})')
            else:
                result.append(f'Guild - Error: cannot access guild (ID: {self.pss_chat_log.guild_id})')
        else:
            result.append(f'Channel - <#{self.pss_chat_log.channel_id}> (ID: {self.pss_chat_log.channel_id})')

        return result
