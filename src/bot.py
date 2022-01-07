import asyncio as _asyncio

import discord as _discord
from discord.ext.commands import Bot as _Bot
from discord.ext.commands import Context as _Context
from discord.ext.commands.errors import CommandInvokeError as _CommandInvokeError
from discord.ext.commands.errors import CommandNotFound as _CommandNotFound
from discord.ext.commands import when_mentioned_or as _when_mentioned_or

from src.model.errors import UnauthorizedChannelError as _UnauthorizedChannelError

from . import bot_settings as _bot_settings
from . import utils as _utils
from .model import setup_model as _setup_model



# ---------- Setup ----------

BOT = _Bot(
    _when_mentioned_or(*_bot_settings.PREFIXES),
    intents=_discord.Intents.all(),
    activity=_discord.activity.Activity(type=_discord.ActivityType.playing, name='vivi help')
)



# ---------- Event handlers ----------

@BOT.event
async def on_command_error(ctx: _Context,
                            err: Exception
                        ) -> None:
    if _bot_settings.THROW_COMMAND_ERRORS:
        raise err

    if isinstance(err, _UnauthorizedChannelError):
        return

    if isinstance(err, _CommandNotFound):
        if not _utils.assert_.authorized_channel(ctx, _bot_settings.AUTHORIZED_CHANNEL_IDS, raise_on_error=False):
            return

    delete_after: float = None
    if isinstance(err, _CommandInvokeError):
        err = err.original
        delete_after = 10.0
    error_type = type(err).__name__
    error_text = (err.args[0] or '') if err.args else ''
    error_lines = [f'**{error_type}**']
    if error_text:
        error_lines.append(error_text)

    await _utils.discord.reply_lines(ctx, error_lines, delete_after)


@BOT.event
async def on_ready() -> None:
    print(f'Bot logged in as {BOT.user.name} ({BOT.user.id})')
    print(f'Bot version: {_bot_settings.VERSION}')
    extensions = '\n'.join(f'- {key.split(".")[-1]}' for key in BOT.extensions.keys())
    print(f'Loaded extensions:\n{extensions}')



# ---------- Module init ----------

async def initialize() -> None:
    await _setup_model()
    BOT.load_extension('src.cogs.about')
    BOT.load_extension('src.cogs.chatlog')
    BOT.load_extension('src.cogs.checks')
    BOT.load_extension('src.cogs.embed')
    BOT.load_extension('src.cogs.roles')
    BOT.load_extension('src.cogs.reactionroles')


def run_bot():
    loop = _asyncio.get_event_loop()
    loop.run_until_complete(initialize())
    BOT.run(_bot_settings.DISCORD_BOT_TOKEN)
