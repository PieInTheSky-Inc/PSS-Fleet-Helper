import json as _json
from typing import List as _List

from discord import Embed as _Embed
from discord.ext.commands import Bot as _Bot
from discord.ext.commands import Cog as _Cog
from discord.ext.commands import Context as _Context
from discord.ext.commands import group as _command_group

from .. import utils as _utils



class EmbedCog(_Cog):
    def __init__(self, bot: _Bot) -> None:
        if not bot:
            raise ValueError('Parameter \'bot\' must not be None.')
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
            embeds.append((await _utils.discord.get_embed_from_definition_or_url(definition_or_url)))
        elif ctx.message.attachments:
            for attachment in ctx.message.attachments:
                attachment_content = (await attachment.read()).decode('utf-8')
                if attachment_content:
                    embeds.append(_json.loads(attachment_content, cls=_utils.discord.EmbedLeovoelDecoder))
        else:
            raise Exception('You need to specify a definition or upload a file containing a definition!')
        for embed in embeds:
            await ctx.reply(embed=embed, mention_author=False)


def setup(bot: _Bot):
    bot.add_cog(EmbedCog(bot))


