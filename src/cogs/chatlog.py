from logging import log
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
from discord.ext.commands import guild_only as _guild_only
from discord.ext.commands import group as _command_group
from discord.utils import escape_markdown as _escape_markdown

from .. import bot_settings as _bot_settings
from .. import utils as _utils
from ..converters import PssChatLoggerConverter as _PssChatLoggerConverter
from ..model import orm as _orm
from ..model.chat_log import PssChatLogger as _PssChatLogger
from ..pssapi import message_service as _message_service
from ..pssapi import device_login as _login



# ---------- Constants ----------



# ---------- Cog ----------

class ChatLoggerCog(_Cog):
    __CHAT_LOG_INTERVAL: float = 30.0

    def __init__(self, bot: _Bot) -> None:
        if not bot:
            raise ValueError('Parameter \'bot\' must not be None.')
        self.__bot = bot
        with _orm.create_session() as session:
            pss_chat_loggers = _orm.get_all(_PssChatLogger, session)
        if pss_chat_loggers:
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
        with _orm.create_session() as session:
            pss_chat_loggers = _orm.get_all(_PssChatLogger, session)
        if not pss_chat_loggers:
            return

        channel_keys: _Dict[str, _List[_PssChatLogger]] = {}
        for pss_chat_logger in pss_chat_loggers:
            channel_keys.setdefault(pss_chat_logger.pss_channel_key, []).append(pss_chat_logger)
        channel_key_count = len(channel_keys.keys())

        remaining_time = ChatLoggerCog.__CHAT_LOG_INTERVAL - (_utils.datetime.get_utc_now() - utc_now).total_seconds()
        delay = remaining_time / channel_key_count * .97

        for channel_key, pss_chat_loggers in channel_keys.items():
            messages = await _message_service.list_messages_for_channel_key(channel_key, access_token)
            messages = sorted(messages, key=lambda x: x.message_id)
            for pss_chat_logger in pss_chat_loggers:
                channel: _TextChannel = await self.bot.fetch_channel(pss_chat_logger.channel_id)
                if channel:
                    messages = [message for message in messages if message.message_id > pss_chat_logger.last_pss_message_id]
                    lines = []
                    for message in messages:
                        user_name_and_fleet = f'**{_escape_markdown(message.user_name)}'
                        if message.fleet_name:
                            user_name_and_fleet += f'** ({_escape_markdown(message.fleet_name)})**'
                        lines.append(f'{user_name_and_fleet}:** {_escape_markdown(message.message)}')
                    if lines:
                        await _utils.discord.send_lines_to_channel(channel, lines)
                        pss_chat_logger.last_pss_message_id = max(message.message_id for message in messages)
                        with _orm.create_session() as session:
                            pss_chat_logger = _orm.merge(session, pss_chat_logger)
                            pss_chat_logger.save(session)
            if channel_key_count > 1:
                await _asyncio.sleep(delay)


    @_guild_only()
    @_command_group(name='chatlog', brief='Configure Chat Logging', invoke_without_command=True)
    async def base(self, ctx: _Context) -> None:
        """
        Configure chat logging on this server. Check out the sub commands.
        """
        if ctx.invoked_subcommand is None:
            _utils.assert_.authorized_channel_or_server_manager(ctx, _bot_settings.AUTHORIZED_CHANNEL_IDS)
            await ctx.send_help('chatlog')


    @_guild_only()
    @base.command(name='add', brief='Add chat logger')
    async def add(self, ctx: _Context, channel_key: str, channel: _TextChannel, *, name: str) -> None:
        """
        Add a chat logger to this server.

        Usage:
          vivi chatlog add [channel_key] [channel] [name]

        Parameters:
          channel_key: Mandatory. The channel key of the PSS chat channel to be logged.
          channel:     Mandatory. The channel the PSS chat shall be logged to.
          name:        Mandatory. A name for this logger to recognize it.

        Examples:
          vivi chatlog add public #log Public Chat - Adds a chat logger for the public chat that will post to the channel #log
        """
        _utils.assert_.authorized_channel_or_server_manager(ctx, _bot_settings.AUTHORIZED_CHANNEL_IDS)
        log_channel = _PssChatLogger.make(ctx.guild.id, channel.id, channel_key, name)
        with _orm.create_session() as session:
            log_channel.create(session)
            pss_chat_loggers = _orm.get_all(_PssChatLogger, session)
        if len(pss_chat_loggers) == 1:
            self.log_chat.start()
        await _utils.discord.reply(ctx, f'Posting messages from channel \'{channel_key}\' to {channel.mention}.')


    @_guild_only()
    @base.command(name='edit', brief='Edit chat logger')
    async def edit(self, ctx: _Context, logger_id: int) -> None:
        """
        Edit a chat logger. An assistant will guide you.

        Usage:
          vivi chatlog edit [logger_id]

        Parameter:
          logger_id: Mandatory. The chat logger to be edited.

        Examples:
          vivi chatlog edit 1 - Edits the chat logger with ID '1' on this server.
        """
        _utils.assert_.authorized_channel_or_server_manager(ctx, _bot_settings.AUTHORIZED_CHANNEL_IDS)
        with _orm.create_session() as session:
            pss_chat_logger = _orm.get_first_filtered_by(
                _PssChatLogger,
                session,
                id=logger_id,
                guild_id=ctx.guild.id,
            )
        if not pss_chat_logger:
            raise Exception(f'A chat log with the ID {logger_id} does not exist on this server.')

        converter = _PssChatLoggerConverter(pss_chat_logger)
        await _utils.discord.reply_lines(ctx, (await converter.to_text()))

        prompt_text = f'Please enter a new [channel_key]'
        new_channel_key, aborted, skipped_new_channel_key = await _utils.discord.inquire_for_text(ctx, prompt_text, abort_text='Aborted', skip_text='Skipped.')

        if aborted:
            await _utils.discord.reply(ctx, f'The request has been cancelled.')
            return

        prompt_text = f'Please enter a new [channel]'
        new_channel, aborted, skipped_new_channel = await _utils.discord.inquire_for_text_channel(ctx, prompt_text, abort_text='Aborted', skip_text='Skipped.')

        if aborted:
            await _utils.discord.reply(ctx, f'The request has been cancelled.')
            return

        prompt_text = f'Please enter a new [name]'
        new_name, aborted, skipped_new_name = await _utils.discord.inquire_for_text(ctx, prompt_text, abort_text='Aborted', skip_text='Skipped.')

        if aborted:
            await _utils.discord.reply(ctx, f'The request has been cancelled.')
            return

        edited = False
        if new_channel_key and not skipped_new_channel_key:
            pss_chat_logger.pss_channel_key = new_channel_key
            edited = True
        if new_channel and not skipped_new_channel:
            pss_chat_logger.channel_id = new_channel.id
            edited = True
        if new_name and not skipped_new_name:
            pss_chat_logger.name = new_name
            edited = True
        if edited:
            with _orm.create_session() as session:
                pss_chat_logger = _orm.merge(session, pss_chat_logger)
                pss_chat_logger.save(session)
            lines = [f'The chat logger has been edited.']
            lines.extend((await converter.to_text()))
            await _utils.discord.reply_lines(ctx, lines)
        else:
            await _utils.discord.reply(ctx, f'The chat logger {pss_chat_logger} has not been edited.')


    @_guild_only()
    @base.group(name='list', brief='List chat loggers for this server', invoke_without_command=True)
    async def list(self, ctx: _Context) -> None:
        """
        Lists all chat logger configured on this server.

        Usage:
          vivi chatlog list
        """
        if ctx.invoked_subcommand is None:
            _utils.assert_.authorized_channel_or_server_manager(ctx, _bot_settings.AUTHORIZED_CHANNEL_IDS)
            with _orm.create_session() as session:
                pss_chat_loggers = _orm.get_all_filtered_by(_PssChatLogger, session, guild_id=ctx.guild.id)
            lines = ['__Listing chat loggers for this Discord server__']
            for pss_chat_logger in pss_chat_loggers:
                converter = _PssChatLoggerConverter(pss_chat_logger)
                definition_lines = await converter.to_text()
                lines.extend(definition_lines)
                lines.append('_ _')
            if len(lines) > 1:
                lines = lines[:-1]
            else:
                lines.append('There are no chat loggers configured for this server.')
            await _utils.discord.reply_lines(ctx, lines)


    @_is_owner()
    @_guild_only()
    @list.command(name='all', brief='List all chat loggers', hidden=True)
    async def list_all(self, ctx: _Context) -> None:
        """
        Lists all chat logger configured on any server.

        Usage:
          vivi chatlog list all
        """
        _utils.assert_.authorized_channel_or_server_manager(ctx, _bot_settings.AUTHORIZED_CHANNEL_IDS)
        with _orm.create_session() as session:
            pss_chat_loggers = _orm.get_all(_PssChatLogger, session)
        lines = ['__Listing all chat loggers__']
        for pss_chat_logger in pss_chat_loggers:
            converter = _PssChatLoggerConverter(pss_chat_logger)
            definition_lines = await converter.to_text(True, self.bot)
            lines.extend(definition_lines)
            lines.append('_ _')
        if len(lines) > 1:
            lines = lines[:-1]
        else:
            lines.append('There are no chat loggers configured.')
        await _utils.discord.reply_lines(ctx, lines)


    @_guild_only()
    @base.command(name='delete', brief='Delete chat logger', aliases=['remove'])
    async def delete(self, ctx: _Context, logger_id: int) -> None:
        """
        Removes a chat logger.

        Usage:
          vivi chatlog delete [logger_id]

        Parameters:
          logger_id: Mandatory. The ID of the chat logger to be deleted.

        Examples:
          vivi chatlog delete 1 - Removes the chat logger with the ID '1'.
        """
        _utils.assert_.authorized_channel_or_server_manager(ctx, _bot_settings.AUTHORIZED_CHANNEL_IDS)
        with _orm.create_session() as session:
            pss_chat_logger: _PssChatLogger = _orm.get_first_filtered_by(
                _PssChatLogger,
                session,
                id=logger_id,
                guild_id=ctx.guild.id
            )
        if not pss_chat_logger:
            raise Exception(f'A chat log with the ID {logger_id} does not exist on this server.')

        converter = _PssChatLoggerConverter(pss_chat_logger)
        await _utils.discord.reply_lines(ctx, (await converter.to_text()))

        prompt_text = f'Do you really want to delete the chat log listed above?'
        delete_log, aborted, _ = await _utils.discord.inquire_for_true_false(ctx, prompt_text)

        if aborted:
            await _utils.discord.reply(ctx, f'The request has been cancelled.')
        elif delete_log:
            with _orm.create_session() as session:
                pss_chat_logger = _orm.get_by_id(_PssChatLogger, session, logger_id)
                pss_chat_logger.delete(session)
                pss_chat_loggerss = _orm.create_session(_PssChatLogger, session)
                if len(pss_chat_loggerss) == 0:
                    self.log_chat.stop()
            await _utils.discord.reply(ctx, f'The chat log has been deleted.')
        else:
            await _utils.discord.reply(ctx, f'The chat log has not been deleted.')


def setup(bot: _Bot):
    bot.add_cog(ChatLoggerCog(bot))