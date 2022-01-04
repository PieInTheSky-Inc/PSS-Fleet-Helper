from discord import Role as _Role
from discord.ext.commands import Bot as _Bot
from discord.ext.commands import Cog as _Cog
from discord.ext.commands import Context as _Context
from discord.ext.commands import group as _command_group
from discord.ext.commands import bot_has_guild_permissions as _bot_has_guild_permissions
from discord.ext.commands import has_guild_permissions as _has_guild_permissions

from .. import utils as _utils





class RolesCog(_Cog):
    def __init__(self, bot: _Bot) -> None:
        if not bot:
            raise ValueError('Parameter \'bot\' must not be None.')
        self.__bot = bot


    @property
    def bot(self) -> _Bot:
        return self.__bot


    @_command_group(name='role', brief='Role management', invoke_without_command=True)
    async def base(self, ctx: _Context) -> None:
        await ctx.send_help('role')


    @_bot_has_guild_permissions(manage_roles=True)
    @_has_guild_permissions(manage_roles=True)
    @base.command(name='add', brief='Add Role to members')
    async def add(self, ctx: _Context, role_id_or_mention: _Role, *, user_ids: str) -> None:
        """
        Add a Role to multiple members of this server.

        Usage:
          vivi role add [role_id_or_mention] [user_id 1] <user_id 2> <user_id ...>

        Parameters:
          role_id_or_mention: Mandatory. An ID or a mention of Role on this server.
          user_id(s): Mandatory. One or more User IDs of members of this server.

        Examples:
          vivi role add @foobar 1 2 3 - Adds the Role @foobar to the members with the IDs 1, 2 & 3
          vivi role add 45 1 2 3 - Adds the Role with ID '45' to the members with the IDs 1, 2 & 3
        """
        user_ids = set(user_ids.split(' '))
        confirmator = _utils.Confirmator(ctx, f'This command will add the role `{role_id_or_mention}` to {len(user_ids)} members!')
        if (await confirmator.wait_for_option_selection()):
            users_added = []
            for user_id in user_ids:
                member = await ctx.guild.fetch_member(int(user_id))
                if member:
                    await member.add_roles(role_id_or_mention)
                    users_added.append(f'{member.display_name} ({user_id})')

            lines = [
                f'Added role {role_id_or_mention} to members:',
                *sorted(users_added)
            ]
            await _utils.discord.reply_lines(ctx, lines)


    @_bot_has_guild_permissions(manage_roles=True)
    @_has_guild_permissions(manage_roles=True)
    @base.command(name='clear', brief='Remove a role from all members')
    async def clear(self, ctx: _Context, role: _Role) -> None:
        """
        Remove a Role from all members of this server.

        Usage:
          vivi role clear [role_id_or_mention]

        Parameters:
          role_id_or_mention: Mandatory. An ID or a mention of Role on this server.

        Examples:
          vivi role clear @foobar - Removes the Role @foobar from all members of this server.
          vivi role clear 45 - Removes the Role with ID '45' from all members of this server.
        """
        members = list(role.members)
        if len(members) > 0:
            confirmator = _utils.Confirmator(ctx, f'This command will remove the role `{role}` from {len(members)} members!')
            if (await confirmator.wait_for_option_selection()):
                users_removed = []
                for member in members:
                    await member.remove_roles(role)
                    users_removed.append(f'{member.display_name} ({member.id})')

                lines = [
                    f'Removed role {role} from members:',
                    *sorted(users_removed)
                ]
                await _utils.discord.reply_lines(ctx, lines)
        else:
            await _utils.discord.reply(ctx, f'There are no members with the role {role}.')


    @_bot_has_guild_permissions(manage_roles=True)
    @_has_guild_permissions(manage_roles=True)
    @base.command(name='remove', brief='Remove a role from specified members')
    async def remove(self, ctx: _Context, role: _Role, *, user_ids: str) -> None:
        """
        Remove a Role from multiple members of this server.

        Usage:
          vivi role remove [role_id_or_mention] [user_id 1] <user_id 2> <user_id ...>

        Parameters:
          role_id_or_mention: Mandatory. An ID or a mention of Role on this server.
          user_id(s): Mandatory. One or more User IDs of members of this server.

        Examples:
          vivi role remove @foobar 1 2 3 - Removes the Role @foobar from Members with the User ID 1, 2 & 3.
          vivi role remove 45 1 2 3 - Removes the Role with ID '45' from Members with the User ID 1, 2 & 3.
        """
        user_ids = set(user_ids.split(' '))
        confirmator = _utils.Confirmator(ctx, f'This command removes the role `{role}` from {len(user_ids)} members.')
        if (await confirmator.wait_for_option_selection()):
            users_removed = []
            for user_id in user_ids:
                member = await ctx.guild.fetch_member(int(user_id))
                await member.remove_roles(role)
                users_removed.append(f'{member.display_name} ({user_id})')

            lines = [
                f'Removed role {role} from members:',
                *sorted(users_removed)
            ]
            await _utils.discord.reply_lines(ctx, lines)


def setup(bot: _Bot):
    bot.add_cog(RolesCog(bot))