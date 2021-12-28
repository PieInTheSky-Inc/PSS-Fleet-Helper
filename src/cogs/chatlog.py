from typing import Dict as _Dict
from typing import List as _List

from discord import Guild as _Guild
from discord import TextChannel as _TextChannel
import discord.ext.tasks as _tasks
from discord.ext.commands import Bot as _Bot
from discord.ext.commands import Cog as _Cog
from discord.ext.commands import Context as _Context
from discord.ext.commands import is_owner as _is_owner
from discord.ext.commands import group as _command_group
from discord.utils import escape_markdown as _escape_markdown

from ..model import orm as _orm
from ..model.chat_log import PssChatLog as _PssChatLog
from ..pssapi import message_service as _message_service
from ..pssapi import login as _login
from ..pssapi.entities import PssMessage as _PssMessage
from .. import utils as _utils



# ---------- Constants ----------

_SESSION = _orm.create_session()



# ---------- Cog ----------

class ChatLogCog(_Cog):
    def __init__(self, bot: _Bot) -> None:
        if not bot:
            raise ValueError('Parameter \'bot\' must not be None.')
        self.__bot = bot
        self.log_chat.start()


    @property
    def bot(self) -> _Bot:
        return self.__bot


    def cog_unload(self):
        self.log_chat.cancel()


    @_tasks.loop(seconds=300.0)
    async def log_chat(self):
        access_token = await _login()
        pss_chat_logs = _orm.get_all(_PssChatLog, _SESSION)
        messages_lookup: _Dict[str, _List[_PssMessage]] = {}
        for pss_chat_log in pss_chat_logs:
            channel: _TextChannel = await self.bot.fetch_channel(pss_chat_log.channel_id)
            if channel:
                if pss_chat_log.pss_channel_key in messages_lookup.keys():
                    messages = messages_lookup[pss_chat_log.pss_channel_key]
                else:
                    messages = await _message_service.list_messages_for_channel_key(pss_chat_log.pss_channel_key, access_token)
                    messages = sorted(messages, key=lambda x: x.message_id)
                    messages_lookup[pss_chat_log.pss_channel_key] = messages

                messages = [message for message in messages if message.message_id > pss_chat_log.last_pss_message_id]
                lines = []
                for message in messages:
                    user_name_and_fleet = f'**{_escape_markdown(message.user_name)}**'
                    if message.fleet_name:
                        user_name_and_fleet += f' ({_escape_markdown(message.fleet_name)})'
                    lines.append(f'{user_name_and_fleet}**:** {_escape_markdown(message.message)}')
                await channel.send(content='\n'.join(lines))
                pss_chat_log.last_pss_message_id = max(message.message_id for message in messages)
                pss_chat_log.save(_SESSION)


    @_command_group(name='chatlog', invoke_without_command=True)
    async def base(self, ctx: _Context) -> None:
        """
        """
        pass


    @base.command(name='add')
    async def add(self, ctx: _Context, channel_key: str, channel: _TextChannel, *, name: str) -> None:
        """
        """
        log_channel = _PssChatLog.make(ctx.guild.id, channel.id, channel_key, name)
        log_channel.create(_SESSION)
        await ctx.reply(f'Posting messages from channel \'{channel_key}\' to {channel.mention}.', mention_author=False)


    @base.group(name='list', invoke_without_command=True)
    async def list(self, ctx: _Context) -> None:
        """
        """
        pass


    @_is_owner()
    @list.command(name='all', hidden=True)
    async def list_all(self, ctx: _Context) -> None:
        """
        """
        pass


    @base.command(name='remove', aliases=['delete'])
    async def remove(self, ctx: _Context, log_id: int) -> None:
        """
        """
        pass


def setup(bot: _Bot):
    bot.add_cog(ChatLogCog(bot))