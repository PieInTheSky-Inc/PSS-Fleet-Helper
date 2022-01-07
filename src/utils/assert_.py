from typing import List as _List

from discord.ext.commands import Context as _Context

from ..model.errors import UnauthorizedChannelError as _UnauthorizedChannelError



def authorized_channel(ctx: _Context, authorized_channel_ids: _List[int], raise_on_error: bool = True) -> bool:
    if ctx.channel.id not in authorized_channel_ids:
        if raise_on_error:
            raise _UnauthorizedChannelError()
        else:
            return False
    return True