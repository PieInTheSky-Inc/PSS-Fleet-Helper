import re as _re
from typing import Optional as _Optional
from typing import Union as _Union

from discord import Emoji as _Emoji
from discord.ext.commands import Context as _Context
import emoji as _emoji






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