import json as _json
from typing import List as _List

from discord import Embed as _Embed
from discord.ext.commands import Bot as _Bot
from discord.ext.commands import Cog as _Cog
from discord.ext.commands import Context as _Context
from discord.ext.commands import group as _command_group

from model import utils as _utils



class EmbedCog(_Cog):
    def __init__(self, bot: _Bot) -> None:
        self.__bot = bot


    @property
    def bot(self) -> _Bot:
        return self.__bot


    @_command_group(name='embed', invoke_without_command=True)
    async def base(self, ctx: _Context, *, definition_or_url: str = None) -> None:
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
            embeds.append((await get_embed_from_definition_or_url(definition_or_url)))
        elif ctx.message.attachments:
            for attachment in ctx.message.attachments:
                attachment_content = (await attachment.read()).decode('utf-8')
                if attachment_content:
                    embeds.append(_json.loads(attachment_content, cls=_utils.discord.EmbedLeovoelDecoder))
        else:
            raise Exception('You need to specify a definition or upload a file containing a definition!')
        for embed in embeds:
            await ctx.reply(embed=embed, mention_author=False)


async def get_embed_from_definition_or_url(definition_or_url: str) -> _Embed:
    try:
        return _json.loads(definition_or_url, cls=_utils.discord.EmbedLeovoelDecoder)
    except _json.JSONDecodeError:
        if 'pastebin.com' in definition_or_url:
            url = _utils.web.get_raw_pastebin(definition_or_url)
        else:
            url = definition_or_url
        url_definition = await _utils.web.get_data_from_url(url)

    try:
        return _json.loads(url_definition, cls=_utils.discord.EmbedLeovoelDecoder)
    except _json.JSONDecodeError:
        raise Exception('This is not a valid embed definition or this url points to a file not containing a valid embed definition.')


def setup(bot: _Bot):
    bot.add_cog(EmbedCog(bot))


