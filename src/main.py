import aiohttp
import asyncio
import json
from typing import List as _List

import discord
from discord import Embed as _Embed
from discord.ext.commands import Bot as _Bot
from discord.ext.commands import Context as _Context
from discord.ext.commands.errors import CommandInvokeError as _CommandInvokeError
from discord.ext.commands import when_mentioned_or as _when_mentioned_or

import app_settings
import model
from model import utils as _utils



# ---------- Setup ----------

BOT = _Bot(
    _when_mentioned_or('vivi '),
    intents=discord.Intents.all(),
    activity=discord.activity.Activity(type=discord.ActivityType.playing, name='vivi help')
)



# ---------- Event handlers ----------

@BOT.event
async def on_command_error(ctx: _Context,
                            err: Exception
                        ) -> None:
    if app_settings.THROW_COMMAND_ERRORS:
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
    print(f'Bot version: {app_settings.VERSION}')
    extensions = '\n'.join(f'- {key}' for key in BOT.extensions.keys())
    print(f'Loaded extensions:\n{extensions}')


@BOT.command(name='embed')
async def cmd_embed(ctx: _Context, *, definition_or_url: str = None) -> None:
    """
    Test the look of an embed.
    Create and edit embed definitions: https://leovoel.github.io/embed-visualizer/

    How to use:
     - Go to https://leovoel.github.io/embed-visualizer/
     - Create an embed as you like it
     - Copy the code on the left starting with the curled opening brackets right next to 'embed:' ending with the second to last curled closing bracket.
     - Paste the code as parameter 'definition_or_url'

    You can also copy the code into a file and attach that file instead, if the definition would be too long to send otherwise.
    You can also copy the code onto pastebin.com and type the url to that file instead.
    You can also type the link to any file on the web containing an embed definition.
    """
    embeds: _List[_Embed] = []
    if definition_or_url:
        try:
            embeds.append(json.loads(definition_or_url, cls=_utils.discord.EmbedLeovoelDecoder))
            url_definition = None
        except json.JSONDecodeError:
            if 'pastebin.com' in definition_or_url:
                url = _utils.web.get_raw_pastebin(definition_or_url)
            else:
                url = definition_or_url
            url_definition = await _utils.web.get_data_from_url(url)

        if url_definition:
            try:
                embeds.append(json.loads(url_definition, cls=_utils.discord.EmbedLeovoelDecoder))
            except json.JSONDecodeError:
                raise Exception('This is not a valid embed definition or this url points to a file not containing a valid embed definition.')
    elif ctx.message.attachments:
        for attachment in ctx.message.attachments:
            attachment_content = (await attachment.read()).decode('utf-8')
            if attachment_content:
                embeds.append(json.loads(attachment_content, cls=_utils.discord.EmbedLeovoelDecoder))
    else:
        raise Exception('You need to specify a definition or upload a file containing a definition!')
    for embed in embeds:
        await ctx.reply(embed=embed, mention_author=False)



# ---------- Module init ----------

async def __initialize() -> None:
    await model.setup_model()
    BOT.load_extension('about')
    BOT.load_extension('checks')
    BOT.load_extension('roles')
    BOT.load_extension('reactionroles')


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(__initialize())
    BOT.run(app_settings.DISCORD_BOT_TOKEN)