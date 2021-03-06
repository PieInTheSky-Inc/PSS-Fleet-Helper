from typing import List as _List

from discord.ext.commands import Context as _Context
from discord.ext.commands.errors import MissingPermissions as _MissingPermissions

from ..model.errors import UnauthorizedChannelError as _UnauthorizedChannelError



def authorized_channel(ctx: _Context, authorized_channel_ids: _List[int], raise_on_error: bool = True) -> bool:
    if ctx.channel.id not in authorized_channel_ids:
        if raise_on_error:
            raise _UnauthorizedChannelError()
        else:
            return False
    return True


def authorized_channel_or_server_manager(ctx: _Context, authorized_channel_ids: _List[int], raise_on_error: bool = True) -> bool:
    if server_manager(ctx, raise_on_error=False):
        return True
    elif authorized_channel(ctx, authorized_channel_ids, raise_on_error=False):
        return True
    if raise_on_error:
        raise Exception([_UnauthorizedChannelError, _MissingPermissions(['manage_guild'])])
    return False


def server_manager(ctx: _Context, raise_on_error: bool = True) -> bool:
    if ctx.guild and ctx.author.guild_permissions.manage_guild:
        if raise_on_error:
            raise _MissingPermissions(['manage_guild'])
        return True
    return False