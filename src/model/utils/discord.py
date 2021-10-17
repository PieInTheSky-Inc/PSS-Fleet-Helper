import re as _re
from typing import Optional as _Optional
from typing import Union as _Union

from discord import Emoji as _Emoji
from discord import TextChannel as _TextChannel
from discord.abc import Messageable as _Messageable
from discord.ext.commands import Context as _Context
import emoji as _emoji



def get_channel(ctx: _Context, s: str) -> _Optional[_Messageable]:
    try:
        channel_id = int(s)
    except:
        channel_id = None
    if channel_id is None:
        match = _re.match('<#(\d+)>', s)
        if match:
            channel_id = int(match.groups()[0])
    if channel_id:
        return ctx.guild.get_channel(channel_id)
    return None


def get_text_channel(ctx: _Context, s: str) -> _Optional[_TextChannel]:
    result: _TextChannel = get_channel(ctx, s)
    if isinstance(result, _TextChannel) and result.permissions_for(ctx.guild.me).view_channel:
        return result
    return None


def get_emoji(ctx: _Context, s: str) -> _Optional[str]:
    emoji_list = _emoji.emoji_lis(s)
    if emoji_list:
        return emoji_list[0]['emoji']
    else:
        match = _re.match('<:\w+:(\d+)>', s)
        if match:
            emoji_id = int(match.groups()[0])
            result = ctx.bot.get_emoji(emoji_id)
            if result and ctx.guild == result.guild:
                return f'<:{result.name}:{result.id}>'
    return None


async def inquire_for_emoji(ctx) -> _Optional[_Union[str, _Emoji]]:
    pass