import asyncio as _asyncio

import discord as _discord
import discord.ext.commands as _commands
import pssapi as _pssapi

from . import bot_settings as _bot_settings
from . import utils as _utils
from . import model as _model


# ---------- Setup ----------

FLEET_HELPER = _model.PssApiDiscordBot(language_key=_pssapi.enums.LanguageKey.ENGLISH)


# ---------- Event handlers ----------


@FLEET_HELPER.event
async def on_command_error(ctx: _commands.Context, err: Exception) -> None:
    original_err = err

    if isinstance(err, _model.errors.UnauthorizedChannelError):
        return

    if isinstance(err, _commands.errors.CommandNotFound):
        if not _utils.assert_.authorized_channel(
            ctx, _bot_settings.AUTHORIZED_CHANNEL_IDS, raise_on_error=False
        ):
            return

    delete_after: float = None
    if isinstance(err, _commands.errors.CommandInvokeError):
        err = err.original
        delete_after = 10.0
    error_type = type(err).__name__
    error_text = (err.args[0] or "") if err.args else ""
    error_lines = [f"**{error_type}**"]
    if error_text:
        error_lines.append(error_text)

    await _utils.discord.reply_lines(ctx, error_lines, delete_after)

    if _bot_settings.THROW_COMMAND_ERRORS:
        raise original_err


@FLEET_HELPER.event
async def on_ready() -> None:
    print(f"Bot logged in as {FLEET_HELPER.user.name} ({FLEET_HELPER.user.id})")
    print(f"Bot version: {_bot_settings.VERSION}")
    print(f"py-cord version: {_discord.__version__}")
    for cog_name, cog_path in _bot_settings.COGS_TO_LOAD.items():
        print(f"Loading cog {cog_name} from extension {cog_path}")
        FLEET_HELPER.load_extension(cog_path)


# ---------- Module init ----------


async def initialize() -> None:
    await _model.setup_model()


def run_bot():
    loop = _asyncio.get_event_loop()
    loop.run_until_complete(initialize())
    FLEET_HELPER.run(_bot_settings.DISCORD_BOT_TOKEN)
