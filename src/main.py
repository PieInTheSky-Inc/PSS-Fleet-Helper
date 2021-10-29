import asyncio as _asyncio

import discord as _discord
from discord.ext.commands import Bot as _Bot
from discord.ext.commands import Context as _Context
from discord.ext.commands.errors import CommandInvokeError as _CommandInvokeError
from discord.ext.commands import when_mentioned_or as _when_mentioned_or

import app_settings as _app_settings
from model import setup_model as _setup_model
from model import utils as _utils



# ---------- Setup ----------

BOT = _Bot(
    _when_mentioned_or('vivi '),
    intents=_discord.Intents.all(),
    activity=_discord.activity.Activity(type=_discord.ActivityType.playing, name='vivi help')
)



# ---------- Event handlers ----------

@BOT.event
async def on_command_error(ctx: _Context,
                            err: Exception
                        ) -> None:
    if _app_settings.THROW_COMMAND_ERRORS:
        raise err

    if isinstance(err, _CommandInvokeError):
        err = err.original
    error_type = type(err).__name__
    error_text = (err.args[0] or '') if err.args else ''
    msg = f'**{error_type}**'
    if error_text:
        msg += f'\n{error_text}'

    await ctx.reply(f'{msg}', mention_author=False)


@BOT.event
async def on_ready() -> None:
    print(f'Bot logged in as {BOT.user.name} ({BOT.user.id})')
    print(f'Bot version: {_app_settings.VERSION}')
    extensions = '\n'.join(f'- {key}' for key in BOT.extensions.keys())
    print(f'Loaded extensions:\n{extensions}')



# ---------- Module init ----------

async def __initialize() -> None:
    await _setup_model()
    BOT.load_extension('about')
    BOT.load_extension('checks')
    BOT.load_extension('embed')
    BOT.load_extension('roles')
    BOT.load_extension('reactionroles')


if __name__ == '__main__':
    loop = _asyncio.get_event_loop()
    loop.run_until_complete(__initialize())
    BOT.run(_app_settings.DISCORD_BOT_TOKEN)
