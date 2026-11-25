import logging

import discord as _discord
import discord.ext.commands as _commands
import psycopg2 as _psycopg2

from .. import bot_settings as _bot_settings
from .. import converters as _converters
from .. import model as _model
from .. import utils as _utils
from .cog_base import CogBase as _CogBase


# ---------- Constants ----------

LOGGER = logging.getLogger("pss_fleet_helper.chatlogger_cog")


# ---------- Cog ----------


class ChatLoggerCog(_CogBase):
    def __init__(self, bot: _model.PssApiDiscordBot) -> None:
        super().__init__(bot)
        self._pss_chat_logger_manager: _model.PssChatLoggerManager = _model.PssChatLoggerManager()
        self._init_errors: list[str] = []

        self.bot.loop.create_task(self.async_init(self._pss_chat_logger_manager, self._init_errors, first_init=True))

    async def async_init(self, pss_chat_logger_manager: _model.PssChatLoggerManager, init_errors: list[str], first_init: bool = False):
        await self.bot.wait_until_ready()

        access_token = _bot_settings.PSS_ACCESS_TOKEN
        user_id = _bot_settings.PSS_USER_ID

        if not access_token or not user_id:
            msg = make_error_message("PSS access token or user ID is not set.", first_init)
            logging.error("[ChatLoggerCog.async_init] {0}", msg)
            init_errors.append(msg)
            return

        try:
            with _model.orm.create_session() as session:
                db_chat_loggers = _model.orm.get_all(_model.db_pss_chat_logger.PssChatLoggerModel, session)
        except _psycopg2.OperationalError as ex:
            logging.error("[ChatLoggerCog.async_init] Could not retrieve configured Chat Loggers from database:\n{0}", ex)
            return

        if not db_chat_loggers:
            msg = make_error_message("No chat loggers configured in the database.", first_init)
            logging.error("[ChatLoggerCog.async_init] {0}", msg)
            init_errors.append(msg)

        for db_chat_logger in db_chat_loggers:
            channel = await fetch_channel(self.bot, db_chat_logger.guild_id, db_chat_logger.channel_id)
            webhook = await get_webhook_from_channel(channel, db_chat_logger.webhook_link)
            if not webhook:
                msg = f"Could not find webhook for channel '{db_chat_logger.channel_id}' on guild '{db_chat_logger.guild_id}' for chat logger '{db_chat_logger.name}' (ID: {db_chat_logger.id})."
                msg = make_error_message(msg, first_init)
                logging.error("[ChatLoggerCog.async_init] {0}", msg)
                init_errors.append(msg)
                continue

            listener = _model.PssDiscordListener(self.bot, webhook)
            pss_chat_logger_manager.subscribe_to_channel(db_chat_logger.pss_channel_key, listener)

        pss_chat_logger_manager.start(access_token, user_id)

    def cog_unload(self):
        if self.watch_log_chat.is_running() and self.watch_log_chat._can_be_cancelled():
            self.watch_log_chat.cancel()

        if self.log_chat.is_running() and self.log_chat._can_be_cancelled():
            self.log_chat.cancel()

    @_commands.guild_only()
    @_commands.group(name="chatlog", brief="Configure Chat Logging", invoke_without_command=True)
    async def base(self, ctx: _commands.Context) -> None:
        """
        Configure chat logging on this server. Check out the sub commands.
        """
        if ctx.invoked_subcommand is None:
            _utils.assert_.authorized_channel_or_server_manager(ctx, _bot_settings.AUTHORIZED_CHANNEL_IDS)
            await ctx.send_help("chatlog")

    @_commands.guild_only()
    @base.command(name="add", brief="Add chat logger")
    async def add(
        self,
        ctx: _commands.Context,
        channel_key: str,
        channel: _discord.TextChannel,
        *,
        name: str,
    ) -> None:
        """
        Add a chat logger to this server.

        Usage:
          fh chatlog add [channel_key] [channel] [name]

        Parameters:
          channel_key: Mandatory. The channel key of the PSS chat channel to be logged.
          channel:     Mandatory. The text channel the PSS chat shall be logged to.
          name:        Mandatory. A name for this logger to recognize it.

        Examples:
          fh chatlog add public #log Public Chat - Adds a chat logger for the public chat that will post to the channel #log
        """
        _utils.assert_.authorized_channel_or_server_manager(ctx, _bot_settings.AUTHORIZED_CHANNEL_IDS)

        if not isinstance(channel, (_discord.TextChannel,)):
            msg = f"Chat Logging is only supported to Text Channels. The channel '{channel}' is not a text channel."
            LOGGER.error(msg)
            raise TypeError(msg)

        webhook = await add_webhook_to_channel(channel, name=name)
        if not webhook:
            msg = f"Failed to create a webhook for the channel '{channel}' (ID: {channel.id}). Please check the bot's permissions."
            LOGGER.error(msg)
            raise Exception(msg)

        pss_chat_logger = _model.db_pss_chat_logger.PssChatLoggerModel.make(ctx.guild.id, channel.id, channel_key, name, webhook.url)
        with _model.orm.create_session() as session:
            pss_chat_logger.create(session)
            _ = _model.orm.get_all(_model.db_pss_chat_logger.PssChatLoggerModel, session)

        listener = _model.PssDiscordListener(self.bot, webhook)
        self._pss_chat_logger_manager.subscribe_to_channel(channel_key, listener)

        lines = [f"Posting messages from channel '{channel_key}' to {channel.mention}."]
        lines.extend((await _converters.PssChatLoggerConverter(pss_chat_logger).to_text()))

        await _utils.discord.reply_lines(ctx, lines)

    @_commands.guild_only()
    @base.command(name="edit", brief="Edit chat logger")
    async def edit(self, ctx: _commands.Context, logger_id: int) -> None:
        """
        Edit a chat logger. An assistant will guide you.

        Usage:
          fh chatlog edit [logger_id]

        Parameter:
          logger_id: Mandatory. The chat logger to be edited.

        Examples:
          fh chatlog edit 1 - Edits the chat logger with ID '1' on this server.
        """
        _utils.assert_.authorized_channel_or_server_manager(ctx, _bot_settings.AUTHORIZED_CHANNEL_IDS)

        with _model.orm.create_session() as session:
            pss_chat_logger = _model.orm.get_first_filtered_by(
                _model.db_pss_chat_logger.PssChatLoggerModel,
                session,
                id=logger_id,
                guild_id=ctx.guild.id,
            )
        if not pss_chat_logger:
            msg = f"A chat log with the ID {logger_id} does not exist on this server."
            LOGGER.error(msg)
            raise Exception(msg)

        old_channel_key, old_channel_id = pss_chat_logger.pss_channel_key, pss_chat_logger.channel_id
        skipped_new_channel_key, skipped_new_channel, skipped_new_name = False, False, False

        converter = _converters.PssChatLoggerConverter(pss_chat_logger)
        await _utils.discord.reply_lines(ctx, (await converter.to_text()))

        prompt_text = "Please enter a new [channel_key]"
        new_channel_key, aborted, skipped_new_channel_key = await _utils.discord.inquire_for_text(ctx, prompt_text, abort_text="Aborted", skip_text="Skipped.")

        if aborted:
            await _utils.discord.reply(ctx, "The request has been cancelled.")
            return

        new_channel = None
        while new_channel is None:
            prompt_text = "Please enter a new [channel] (no forum channels or threads supported)"
            new_channel, aborted, skipped_new_channel = await _utils.discord.inquire_for_text_channel(ctx, prompt_text, abort_text="Aborted", skip_text="Skipped.")
            if not isinstance(new_channel, _discord.TextChannel):
                await _utils.discord.reply(ctx, f"Chat Logging is only supported to Text Channels. The channel '{new_channel}' is not a text channel.")
                new_channel = None

            if aborted:
                await _utils.discord.reply(ctx, "The request has been cancelled.")
                return

        prompt_text = "Please enter a new [name]"
        new_name, aborted, skipped_new_name = await _utils.discord.inquire_for_text(ctx, prompt_text, abort_text="Aborted", skip_text="Skipped.")

        if aborted:
            await _utils.discord.reply(ctx, "The request has been cancelled.")
            return

        channel_key_changed = new_channel_key and not skipped_new_channel_key
        discord_channel_changed = new_channel and not skipped_new_channel
        name_changed = new_name and not skipped_new_name

        if channel_key_changed or discord_channel_changed or name_changed:
            if name_changed:
                pss_chat_logger.name = new_name

            if channel_key_changed or discord_channel_changed:
                old_webhook = await get_webhook_from_channel(self.bot.get_channel(pss_chat_logger.channel_id), pss_chat_logger.webhook_link)
                old_channel = self.bot.get_channel(old_channel_id)
                new_webhook = None

                if channel_key_changed:
                    pss_chat_logger.pss_channel_key = new_channel_key

                if discord_channel_changed:
                    new_webhook = await add_webhook_to_channel(new_channel, name=pss_chat_logger.name)
                    pss_chat_logger.webhook_link = new_webhook.url
                    pss_chat_logger.channel_id = new_channel.id

                self._pss_chat_logger_manager.unsubscribe_from_channel(old_channel_key, old_webhook.url)
                self._pss_chat_logger_manager.subscribe_to_channel(pss_chat_logger.pss_channel_key, _model.PssDiscordListener(self.bot, new_webhook or old_webhook))
                if old_channel:
                    await delete_webhook_from_channel(pss_chat_logger.webhook_link, old_channel)

            with _model.orm.create_session() as session:
                pss_chat_logger = _model.orm.merge(session, pss_chat_logger)
                pss_chat_logger.save(session)

            lines = ["The chat logger has been edited."]
            lines.extend((await converter.to_text()))

            await _utils.discord.reply_lines(ctx, lines)
        else:
            await _utils.discord.reply(ctx, f"The chat logger {pss_chat_logger} has not been edited.")

    @_commands.guild_only()
    @base.group(
        name="list",
        brief="List chat loggers for this server",
        invoke_without_command=True,
    )
    async def list(self, ctx: _commands.Context) -> None:
        """
        Lists all chat logger configured on this server.

        Usage:
          fh chatlog list
        """
        if ctx.invoked_subcommand is None:
            _utils.assert_.authorized_channel_or_server_manager(ctx, _bot_settings.AUTHORIZED_CHANNEL_IDS)
            with _model.orm.create_session() as session:
                pss_chat_loggers = _model.orm.get_all_filtered_by(_model.db_pss_chat_logger.PssChatLoggerModel, session, guild_id=ctx.guild.id)

            lines = ["_listing chat loggers for this Discord server_"]
            for pss_chat_logger in pss_chat_loggers:
                converter = _converters.PssChatLoggerConverter(pss_chat_logger)
                definition_lines = await converter.to_text()
                lines.extend(definition_lines)
                lines.append("_ _")

            if len(lines) > 1:
                lines = lines[:-1]
            else:
                lines.append("There are no chat loggers configured for this server.")

            await _utils.discord.reply_lines(ctx, lines)

    @_commands.is_owner()
    @_commands.guild_only()
    @list.command(name="all", brief="List all chat loggers", hidden=True)
    async def list_all(self, ctx: _commands.Context) -> None:
        """
        Lists all chat logger configured on any server.

        Usage:
          fh chatlog list all
        """
        _utils.assert_.authorized_channel_or_server_manager(ctx, _bot_settings.AUTHORIZED_CHANNEL_IDS)
        with _model.orm.create_session() as session:
            pss_chat_loggers = _model.orm.get_all(_model.db_pss_chat_logger.PssChatLoggerModel, session)
        lines = ["_listing all chat loggers__"]
        for pss_chat_logger in pss_chat_loggers:
            converter = _converters.PssChatLoggerConverter(pss_chat_logger)
            definition_lines = await converter.to_text(True, self.bot)
            lines.extend(definition_lines)
            lines.append("_ _")
        if len(lines) > 1:
            lines = lines[:-1]
        else:
            lines.append("There are no chat loggers configured.")
        await _utils.discord.reply_lines(ctx, lines)

    @_commands.guild_only()
    @base.command(name="delete", brief="Delete chat logger", aliases=["remove"])
    async def delete(self, ctx: _commands.Context, logger_id: int) -> None:
        """
        Removes a chat logger.

        Usage:
          fh chatlog delete [logger_id]

        Parameters:
          logger_id: Mandatory. The ID of the chat logger to be deleted.

        Examples:
          fh chatlog delete 1 - Removes the chat logger with the ID '1'.
        """
        _utils.assert_.authorized_channel_or_server_manager(ctx, _bot_settings.AUTHORIZED_CHANNEL_IDS)
        with _model.orm.create_session() as session:
            pss_chat_logger: _model.db_pss_chat_logger.PssChatLoggerModel = _model.orm.get_first_filtered_by(
                _model.db_pss_chat_logger.PssChatLoggerModel,
                session,
                id=logger_id,
                guild_id=ctx.guild.id,
            )
        if not pss_chat_logger:
            msg = f"A chat log with the ID {logger_id} does not exist on this server."
            LOGGER.error(msg)
            raise ValueError(msg)

        converter = _converters.PssChatLoggerConverter(pss_chat_logger)
        await _utils.discord.reply_lines(ctx, (await converter.to_text()))

        prompt_text = "Do you really want to delete the chat log listed above?"
        delete_log, aborted, _ = await _utils.discord.inquire_for_true_false(ctx, prompt_text)

        if aborted:
            await _utils.discord.reply(ctx, "The request has been cancelled.")
        elif delete_log:
            channel = self.bot.get_channel(pss_chat_logger.channel_id)
            await delete_webhook_from_channel(pss_chat_logger.webhook_link, channel)
            self._pss_chat_logger_manager.unsubscribe_from_channel(pss_chat_logger.pss_channel_key, pss_chat_logger.webhook_link)

            with _model.orm.create_session() as session:
                pss_chat_logger = _model.orm.get_by_id(_model.db_pss_chat_logger.PssChatLoggerModel, session, logger_id)
                session.delete(pss_chat_logger)
                session.commit()

            await _utils.discord.reply(ctx, "The chat log has been deleted.")
        else:
            await _utils.discord.reply(ctx, "The chat log has not been deleted.")

    @_commands.is_owner()
    @base.command(name="errors", brief="Show errors occuring during cog initialization")
    async def errors(self, ctx: _commands.Context) -> None:
        """
        Shows errors that occurred during the initialization of the chat logger cog.

        Usage:
          fh chatlog errors
        """
        _utils.assert_.authorized_channel_or_server_manager(ctx, _bot_settings.AUTHORIZED_CHANNEL_IDS)
        if not self._init_errors:
            await _utils.discord.reply(ctx, "No errors occurred during cog initialization.")
            return

        lines = ["## Cog initialization errors"]
        lines.extend(self._init_errors)
        await _utils.discord.reply_lines(ctx, lines)


def setup(bot: _model.PssApiDiscordBot):
    bot.add_cog(ChatLoggerCog(bot))


async def delete_webhook_from_channel(webhook_link: str, channel: _discord.TextChannel):
    if channel and isinstance(channel, _discord.TextChannel):
        for webhook in await channel.webhooks():
            if webhook.url == webhook_link:
                await webhook.delete(reason="Deleted by Fleet Helper")
                break


async def add_webhook_to_channel(channel: _discord.TextChannel, name: str | None = None) -> _discord.Webhook | None:
    if channel and isinstance(channel, _discord.TextChannel):
        if not name:
            name = "PSS Chat Logger"
        try:
            webhook = await channel.create_webhook(name=name, reason="Created by Fleet Helper")
        except (_discord.NotFound, _discord.Forbidden, _discord.HTTPException) as ex:
            msg = f"[add_webhook_to_channel] Could not create webhook: {0}"
            LOGGER.error(msg, ex)
        return webhook
    return None


async def get_webhook_from_channel(channel: _discord.TextChannel, webhook_link: str) -> _discord.Webhook | None:
    if channel and isinstance(channel, _discord.TextChannel):
        try:
            channel_webhooks = await channel.webhooks()
        except _discord.Forbidden:
            msg = f"[get_webhook_from_channel] Bot does not have permission to access webhooks in channel '{channel}' (ID: {channel.id})."
            LOGGER.error(msg)
            return None

        for webhook in channel_webhooks:
            if webhook.url == webhook_link:
                return webhook
    return None


async def convert_to_webhook(chat_logger: _model.db_pss_chat_logger.PssChatLoggerModel, bot: _model.PssApiDiscordBot) -> str | None:
    try:
        channel = await bot.fetch_channel(chat_logger.channel_id)
    except (_discord.NotFound, _discord.Forbidden, _discord.HTTPException):
        msg = f"[convert_to_webhook] Could not fetch channel with ID {chat_logger.channel_id} for chat logger '{chat_logger.name}' (ID: {chat_logger.id})."
        LOGGER.error(msg)
        return None

    try:
        webhook = await add_webhook_to_channel(channel, name=chat_logger.name)
    except _discord.Forbidden:
        msg = f"[convert_to_webhook] Bot does not have permission to create a webhook in channel '{channel}' (ID: {chat_logger.channel_id}) for chat logger '{chat_logger.name}' (ID: {chat_logger.id})."
        LOGGER.error(msg)
        return None

    return webhook.url


async def migrate_to_webhooks(bot: _model.PssApiDiscordBot):
    already_migrated, _ = await _model.database.get_setting("chat_logger_migrated_to_webhooks")
    if already_migrated:
        return

    with _model.orm.create_session() as session:
        pss_chat_loggers = _model.orm.get_all(_model.db_pss_chat_logger.PssChatLoggerModel, session)
    for pss_chat_logger in pss_chat_loggers:
        if not pss_chat_logger.webhook_link:
            print("Migrating chat logger to webhook:", pss_chat_logger)
            webhook_link = await convert_to_webhook(pss_chat_logger, bot)
            if not webhook_link:
                continue

            pss_chat_logger.webhook_link = webhook_link
            print("Webhook link for chat logger:", pss_chat_logger.webhook_link)
            with _model.orm.create_session() as session:
                pss_chat_logger = _model.orm.merge(session, pss_chat_logger)
                pss_chat_logger.save(session)
                session.commit()
    await _model.database.set_setting("chat_logger_migrated_to_webhooks", True)


def make_error_message(msg: str, first_init: bool = False) -> str:
    if first_init:
        msg = f"Initial init: {msg}"
    return f"{_utils.format.datetime(_utils.datetime.get_utc_now())} - {msg}"


async def fetch_channel(bot: _discord.Bot, guild_id: int, channel_id: int) -> _discord.Channel | None:
    try:
        guild = bot.get_guild(guild_id)
    except (_discord.NotFound, _discord.Forbidden, _discord.HTTPException) as ex:
        pass

    if not guild:
        try:
            guild = await bot.fetch_guild(guild_id)
        except (_discord.NotFound, _discord.Forbidden, _discord.HTTPException) as ex:
            LOGGER.error(f"Could not get or fetch guild with ID '{guild_id}'")
            return

    try:
        channel = guild.get_channel(channel_id)
    except (_discord.NotFound, _discord.Forbidden, _discord.HTTPException) as ex:
        pass

    if not channel:
        try:
            channel = await guild.fetch_channel(channel_id)
        except (_discord.NotFound, _discord.Forbidden, _discord.HTTPException) as ex:
            LOGGER.error(f"Could not get or fetch channel with ID '{channel_id}' from guild '{guild.name}' (ID: {guild_id}).")
            return

    return channel
