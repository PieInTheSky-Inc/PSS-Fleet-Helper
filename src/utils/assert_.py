from typing import List as _List

from discord import Member as _Member
from discord import Role as _Role
from discord.ext.commands import Context as _Context
from discord.ext.commands.errors import MissingPermissions as _MissingPermissions

from ..model.errors import UnauthorizedChannelError as _UnauthorizedChannelError



def authorized_channel(ctx: _Context, authorized_channel_ids: _List[int], raise_on_error: bool = True) -> bool:
    """
    Asserts that the command has been issued in an authorized channel.
    """
    if ctx.channel.id not in authorized_channel_ids:
        if raise_on_error:
            raise _UnauthorizedChannelError()
        else:
            return False
    return True


def authorized_channel_or_server_manager(ctx: _Context, authorized_channel_ids: _List[int], raise_on_error: bool = True) -> bool:
    """
    Asserts that the command has been issued in an authorized channel or by a server manager.
    """
    if server_manager(ctx, raise_on_error=False):
        return True
    elif authorized_channel(ctx, authorized_channel_ids, raise_on_error=False):
        return True
    if raise_on_error:
        raise Exception([_UnauthorizedChannelError, _MissingPermissions(['manage_guild'])])
    return False


def can_add_remove_role(me: _Member, role: _Role, action: str = None, raise_on_error: bool = True) -> bool:
    """
    Asserts that the bot is allowed to add or remove the specified role.
    """
    if role.position < me.top_role.position:
        return True
    if raise_on_error:
        action = action or 'add/remove'
        raise Exception(f'I can\'t {action} the role {role.mention}: it is either my top role or above.')
    return False


def server_manager(ctx: _Context, raise_on_error: bool = True) -> bool:
    """
    Asserts that the command has been issued by a server manager.
    """
    if ctx.guild and ctx.author.guild_permissions.manage_guild:
        if raise_on_error:
            raise _MissingPermissions(['manage_guild'])
        return True
    return False