import datetime as _datetime
from typing import Dict as _Dict
from typing import List as _List

import asyncio as _asyncio
import discord as _discord
import discord.ext.tasks as _tasks
import discord.ext.commands as _commands
import psycopg2 as _psycopg2
import pssapi as _pssapi

from .cog_base import CogBase as _CogBase
from .. import bot_settings as _bot_settings
from .. import utils as _utils
from .. import converters as _converters
from .. import model as _model




# ---------- Constants ----------



# ---------- Cog ----------

class ChatLogger(_CogBase):
    __CHAT_LOG_INTERVAL: float = 100.0

    def __init__(self, bot: _model.PssApiDiscordBot) -> None:
        super().__init__(bot)
        self.__last_log_chat_run_at: _datetime.datetime = None
        self.watch_log_chat.start()


    def cog_unload(self):
        if self.watch_log_chat.is_running() and self.watch_log_chat._can_be_cancelled():
            self.watch_log_chat.cancel()

        if self.log_chat.is_running() and self.log_chat._can_be_cancelled():
            self.log_chat.cancel()


    @_tasks.loop(seconds=__CHAT_LOG_INTERVAL/4)
    async def watch_log_chat(self):
        utc_now = _utils.datetime.get_utc_now()

        if not self.log_chat.is_running():
            self.log_chat.start()
            return

            if self.__last_log_chat_run_at is None:
                self.log_chat.start()
            elif (utc_now - self.__last_log_chat_run_at).total_seconds > ChatLogger.__CHAT_LOG_INTERVAL:
                try:
                    self.log_chat.cancel()
                    print('[watch_log_chat] Successfully cancelled the task \'log_chat\'.')
                except Exception as ex:
                    print('[watch_log_chat] Could not cancel the task \'log_chat\':')
                    print(ex)
                
                if not self.log_chat.is_running():
                    try:
                        self.log_chat.start()
                        print('[watch_log_chat] Successfully started the task \'log_chat\'.')
                    except Exception as ex:
                        print('[watch_log_chat] Could not start the task \'log_chat\':')
                        print(ex)


    @_tasks.loop(seconds=__CHAT_LOG_INTERVAL)
    async def log_chat(self):
        utc_now = _utils.datetime.get_utc_now()
        self.__last_log_chat_run_at = utc_now

        pss_chat_loggers: _List[_model.chat_log.PssChatLogger] = []
        try:
            with _model.orm.create_session() as session:
                pss_chat_loggers = _model.orm.get_all(_model.chat_log.PssChatLogger, session)
            if not pss_chat_loggers:
                return
        except _psycopg2.OperationalError as ex:
            print('[log_chat] Could not retrieve configured Chat Loggers from database:')
            print(ex)
            return

        try:
            access_token = await self.bot.pssapi_login()
        except _pssapi.utils.exceptions.PssApiError as ex:
            print(ex)
            return

        channel_keys: _Dict[str, _List[_model.chat_log.PssChatLogger]] = {}
        for pss_chat_logger in pss_chat_loggers:
            channel_keys.setdefault(pss_chat_logger.pss_channel_key, []).append(pss_chat_logger)
        channel_key_count = len(channel_keys.keys())

        remaining_time = ChatLogger.__CHAT_LOG_INTERVAL - (_utils.datetime.get_utc_now() - utc_now).total_seconds()
        delay = remaining_time / channel_key_count * (1 - channel_key_count * .01)

        for channel_key, pss_chat_loggers in channel_keys.items():
            tries = 2
            while tries > 0:
                try:
                    messages = await self.bot.pssapi_client.message_service.list_messages_for_channel_key(access_token, channel_key)
                    break
                except _pssapi.utils.exceptions.ServerMaintenanceError:
                    print(f'Server is under maintenance.')
                    return
                except _pssapi.utils.exceptions.PssApiError as ex:
                    print(f'Could not get messages for channel key \'{channel_key}\':\n{ex}')
                    messages = None
                    tries -= 1
                    await _asyncio.sleep(.2)
            if messages:
                messages = sorted(messages, key=lambda x: x.message_id)
                for pss_chat_logger in pss_chat_loggers:
                    channel: _discord.TextChannel = self.bot.get_channel(pss_chat_logger.channel_id)
                    if channel:
                        messages = [message for message in messages if message.message_id > pss_chat_logger.last_pss_message_id]
                        lines = []
                        for message in messages:
                            user_name_and_fleet = f'**{_utils.discord.escape_markdown_and_mentions(message.user_name)}'
                            if message.alliance_name:
                                user_name_and_fleet += f'** ({_utils.discord.escape_markdown_and_mentions(message.alliance_name)})**'
                            lines.append(f'{user_name_and_fleet}:** {_utils.discord.escape_markdown_and_mentions(message.message)}')
                        if lines:
                            try:
                                await _utils.discord.send_lines_to_channel(channel, lines)
                            except:
                                continue
                            pss_chat_logger.last_pss_message_id = max(message.message_id for message in messages)
                try:
                    with _model.orm.create_session() as session:
                        for pss_chat_logger in pss_chat_loggers:
                            pss_chat_logger = _model.orm.merge(session, pss_chat_logger)
                            pss_chat_logger.save(session)
                except _psycopg2.OperationalError as ex:
                    print('[log_chat] Could not update Chat Loggers in database:')
                    print(ex)

            if channel_key_count > 1:
                await _asyncio.sleep(delay)


    @_commands.guild_only()
    @_commands.group(name='chatlog', brief='Configure Chat Logging', invoke_without_command=True)
    async def base(self, ctx: _commands.Context) -> None:
        """
        Configure chat logging on this server. Check out the sub commands.
        """
        if ctx.invoked_subcommand is None:
            _utils.assert_.authorized_channel_or_server_manager(ctx, _bot_settings.AUTHORIZED_CHANNEL_IDS)
            await ctx.send_help('chatlog')


    @_commands.guild_only()
    @base.command(name='add', brief='Add chat logger')
    async def add(self, ctx: _commands.Context, channel_key: str, channel: _discord.TextChannel, *, name: str) -> None:
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
        log_channel = _model.chat_log.PssChatLogger.make(ctx.guild.id, channel.id, channel_key, name)
        with _model.orm.create_session() as session:
            log_channel.create(session)
            pss_chat_loggers = _model.orm.get_all(_model.chat_log.PssChatLogger, session)
        await _utils.discord.reply(ctx, f'Posting messages from channel \'{channel_key}\' to {channel.mention}.')


    @_commands.guild_only()
    @base.command(name='edit', brief='Edit chat logger')
    async def edit(self, ctx: _commands.Context, logger_id: int) -> None:
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
        with _model.orm.create_session() as session:
            pss_chat_logger = _model.orm.get_first_filtered_by(
                _model.chat_log.PssChatLogger,
                session,
                id=logger_id,
                guild_id=ctx.guild.id,
            )
        if not pss_chat_logger:
            raise Exception(f'A chat log with the ID {logger_id} does not exist on this server.')

        converter = _converters.PssChatLoggerConverter(pss_chat_logger)
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
            with _model.orm.create_session() as session:
                pss_chat_logger = _model.orm.merge(session, pss_chat_logger)
                pss_chat_logger.save(session)
            lines = [f'The chat logger has been edited.']
            lines.extend((await converter.to_text()))
            await _utils.discord.reply_lines(ctx, lines)
        else:
            await _utils.discord.reply(ctx, f'The chat logger {pss_chat_logger} has not been edited.')


    @_commands.guild_only()
    @base.group(name='list', brief='List chat loggers for this server', invoke_without_command=True)
    async def list(self, ctx: _commands.Context) -> None:
        """
        Lists all chat logger configured on this server.

        Usage:
          vivi chatlog list
        """
        if ctx.invoked_subcommand is None:
            _utils.assert_.authorized_channel_or_server_manager(ctx, _bot_settings.AUTHORIZED_CHANNEL_IDS)
            with _model.orm.create_session() as session:
                pss_chat_loggers = _model.orm.get_all_filtered_by(_model.chat_log.PssChatLogger, session, guild_id=ctx.guild.id)
            lines = ['__Listing chat loggers for this Discord server__']
            for pss_chat_logger in pss_chat_loggers:
                converter = _converters.PssChatLoggerConverter(pss_chat_logger)
                definition_lines = await converter.to_text()
                lines.extend(definition_lines)
                lines.append('_ _')
            if len(lines) > 1:
                lines = lines[:-1]
            else:
                lines.append('There are no chat loggers configured for this server.')
            await _utils.discord.reply_lines(ctx, lines)


    @_commands.is_owner()
    @_commands.guild_only()
    @list.command(name='all', brief='List all chat loggers', hidden=True)
    async def list_all(self, ctx: _commands.Context) -> None:
        """
        Lists all chat logger configured on any server.

        Usage:
          vivi chatlog list all
        """
        _utils.assert_.authorized_channel_or_server_manager(ctx, _bot_settings.AUTHORIZED_CHANNEL_IDS)
        with _model.orm.create_session() as session:
            pss_chat_loggers = _model.orm.get_all(_model.chat_log.PssChatLogger, session)
        lines = ['__Listing all chat loggers__']
        for pss_chat_logger in pss_chat_loggers:
            converter = _converters.PssChatLoggerConverter(pss_chat_logger)
            definition_lines = await converter.to_text(True, self.bot)
            lines.extend(definition_lines)
            lines.append('_ _')
        if len(lines) > 1:
            lines = lines[:-1]
        else:
            lines.append('There are no chat loggers configured.')
        await _utils.discord.reply_lines(ctx, lines)


    @_commands.guild_only()
    @base.command(name='delete', brief='Delete chat logger', aliases=['remove'])
    async def delete(self, ctx: _commands.Context, logger_id: int) -> None:
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
        with _model.orm.create_session() as session:
            pss_chat_logger: _model.chat_log.PssChatLogger = _model.orm.get_first_filtered_by(
                _model.chat_log.PssChatLogger,
                session,
                id=logger_id,
                guild_id=ctx.guild.id
            )
        if not pss_chat_logger:
            raise Exception(f'A chat log with the ID {logger_id} does not exist on this server.')

        converter = _converters.PssChatLoggerConverter(pss_chat_logger)
        await _utils.discord.reply_lines(ctx, (await converter.to_text()))

        prompt_text = f'Do you really want to delete the chat log listed above?'
        delete_log, aborted, _ = await _utils.discord.inquire_for_true_false(ctx, prompt_text)

        if aborted:
            await _utils.discord.reply(ctx, f'The request has been cancelled.')
        elif delete_log:
            with _model.orm.create_session() as session:
                pss_chat_logger = _model.orm.get_by_id(_model.chat_log.PssChatLogger, session, logger_id)
                session.delete(pss_chat_logger)
                session.commit()
            await _utils.discord.reply(ctx, f'The chat log has been deleted.')
        else:
            await _utils.discord.reply(ctx, f'The chat log has not been deleted.')


def setup(bot: _model.PssApiDiscordBot):
    bot.add_cog(ChatLogger(bot))