from typing import Dict as _Dict
from typing import List as _List

import asyncio as _asyncio
from discord import Guild as _Guild
from discord import TextChannel as _TextChannel
import discord.ext.tasks as _tasks
from discord.ext.commands import Bot as _Bot
from discord.ext.commands import Cog as _Cog
from discord.ext.commands import Context as _Context
from discord.ext.commands import is_owner as _is_owner
from discord.ext.commands import group as _command_group
from discord.utils import escape_markdown as _escape_markdown

from ..converters import PssChatLogConverter as _PssChatLogConverter
from ..model import orm as _orm
from ..model.chat_log import PssChatLog as _PssChatLog
from ..pssapi import message_service as _message_service
from ..pssapi import login as _login
from .. import utils as _utils



# ---------- Constants ----------

_SESSION = _orm.create_session()



# ---------- Cog ----------

class ChatLogCog(_Cog):
    __CHAT_LOG_INTERVAL: float = 60.0

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


    @_tasks.loop(seconds=__CHAT_LOG_INTERVAL)
    async def log_chat(self):
        utc_now = _utils.datetime.get_utc_now()
        access_token = await _login()
        pss_chat_logs = _orm.get_all(_PssChatLog, _SESSION)
        channel_keys: _Dict[str, _List[_PssChatLog]] = {}
        for pss_chat_log in pss_chat_logs:
            channel_keys.setdefault(pss_chat_log.pss_channel_key, []).append(pss_chat_log)
        channel_key_count = len(channel_keys.keys())

        delay = (ChatLogCog.__CHAT_LOG_INTERVAL - (_utils.datetime.get_utc_now() - utc_now).total_seconds()) / channel_key_count * .97

        for channel_key, pss_chat_logs in channel_keys.items():
            messages = await _message_service.list_messages_for_channel_key(channel_key, access_token)
            messages = sorted(messages, key=lambda x: x.message_id)
            for pss_chat_log in pss_chat_logs:
                channel: _TextChannel = await self.bot.fetch_channel(pss_chat_log.channel_id)
                if channel:
                    messages = [message for message in messages if message.message_id > pss_chat_log.last_pss_message_id]
                    lines = []
                    for message in messages:
                        user_name_and_fleet = f'**{_escape_markdown(message.user_name)}**'
                        if message.fleet_name:
                            user_name_and_fleet += f' ({_escape_markdown(message.fleet_name)})'
                        lines.append(f'{user_name_and_fleet}**:** {_escape_markdown(message.message)}')
                    if lines:
                        await channel.send(content='\n'.join(lines))
                        pss_chat_log.last_pss_message_id = max(message.message_id for message in messages)
                        pss_chat_log.save(_SESSION)
            if channel_key_count > 1:
                await _asyncio.sleep(delay)


    @_command_group(name='chatlog', invoke_without_command=True)
    async def base(self, ctx: _Context) -> None:
        """
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help('chatlog')


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
        pss_chat_logs = _orm.get_all(_PssChatLog, _SESSION)
        lines = ['__Listing chat loggers for this Discord server__']
        for pss_chat_log in pss_chat_logs:
            converter = _PssChatLogConverter(pss_chat_log)
            definition_lines = await converter.to_text(False)
            lines.extend(definition_lines)
            lines.append('_ _')
        if len(lines) > 1:
            lines = lines[:-1]
        else:
            lines.append('There are no chat loggers configured for this server.')
        await ctx.reply('\n'.join(lines), mention_author=False)


    @_is_owner()
    @list.command(name='all', hidden=True)
    async def list_all(self, ctx: _Context) -> None:
        """
        """
        pss_chat_logs = _orm.get_all(_PssChatLog, _SESSION)
        lines = ['__Listing all chat loggers__']
        for pss_chat_log in pss_chat_logs:
            converter = _PssChatLogConverter(pss_chat_log)
            definition_lines = await converter.to_text(True, self.bot)
            lines.extend(definition_lines)
            lines.append('_ _')
        if len(lines) > 1:
            lines = lines[:-1]
        else:
            lines.append('There are no chat loggers configured.')
        await ctx.reply('\n'.join(lines), mention_author=False)


    @base.command(name='remove', aliases=['delete'])
    async def remove(self, ctx: _Context, log_id: int) -> None:
        """
        """
        called_by_owner = await self.bot.is_owner(ctx.author)
        pss_chat_log: _PssChatLog = _orm.get_query(_PssChatLog, _SESSION).filter_by(id=log_id).first()
        if not pss_chat_log or (pss_chat_log.guild_id != ctx.guild.id and not called_by_owner):
            raise Exception(f'A chat log with the ID {log_id} does not exist on this server.')

        converter = _PssChatLogConverter(pss_chat_log)
        definition_lines = await converter.to_text(called_by_owner, self.bot)
        await ctx.reply('\n'.join(definition_lines), mention_author=False)

        prompt_text = f'Do you really want to remove the chat log listed above?'
        remove_log, aborted, _ = await _utils.discord.inquire_for_true_false(ctx, prompt_text)

        if aborted:
            await ctx.reply(f'The request has been cancelled.', mention_author=False)
        elif remove_log:
            pss_chat_log.delete(_SESSION)
            await ctx.reply(f'The chat log has been deleted.', mention_author=False)
        else:
            await ctx.reply(f'The chat log has not been deleted.', mention_author=False)


def setup(bot: _Bot):
    bot.add_cog(ChatLogCog(bot))