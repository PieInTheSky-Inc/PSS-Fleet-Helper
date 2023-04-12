from discord import Member as _Member
from discord import Role as _Role
from discord.ext.commands import Bot as _Bot
from discord.ext.commands import Context as _Context
from discord.ext.commands import group as _command_group
from discord.ext.commands import bot_has_guild_permissions as _bot_has_guild_permissions
from discord.ext.commands import has_guild_permissions as _has_guild_permissions

from .cog_base import CogBase as _CogBase
from .. import bot_settings as _bot_settings
from .. import utils as _utils



class RoleManagement(_CogBase):
    @_command_group(name='role', aliases=['roles'], brief='Role management', invoke_without_command=True)
    async def role(self, ctx: _Context) -> None:
        if ctx.invoked_subcommand is None:
            _utils.assert_.authorized_channel_or_server_manager(ctx, _bot_settings.AUTHORIZED_CHANNEL_IDS)
            await ctx.send_help('role')


    @_bot_has_guild_permissions(manage_roles=True)
    @_has_guild_permissions(manage_roles=True)
    @role.command(name='add', brief='Add Role to members')
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
        _utils.assert_.authorized_channel_or_server_manager(ctx, _bot_settings.AUTHORIZED_CHANNEL_IDS)

        if role_id_or_mention.position >= ctx.me.top_role.position:
            raise Exception(f'Cannot add the role {role_id_or_mention.mention}: it is either my top role or above.')

        user_ids = set(user_ids.split(' '))
        reason = f'User {ctx.author.display_name} (ID: {ctx.author.id}) issued command: role add'
        confirmator = _utils.Confirmator(ctx, f'This command will add the role `{role_id_or_mention}` to {len(user_ids)} members!')
        if (await confirmator.wait_for_option_selection()):
            users_added = []
            not_added = []
            for user_id in user_ids:
                member = ctx.guild.get_member(int(user_id))
                if member:
                    await member.add_roles(role_id_or_mention, reason=reason)
                    users_added.append(f'{member.display_name} ({user_id})')
                else:
                    not_added.append(user_id)

            lines = ['The command completed successfully.']
            if users_added:
                lines.extend((
                    f'Added role {role_id_or_mention} to {len(users_added)} members:',
                    *users_added
                ))
            if not_added:
                lines.extend((
                    f'Could not add role to {len(not_added)} users with ID:',
                    *not_added
                ))
            await _utils.discord.reply_lines(ctx, lines)
    

    @_bot_has_guild_permissions(manage_roles=True)
    @_has_guild_permissions(manage_roles=True)
    @role.group(name='addtorole', brief='Add Role to members with certain role(s)', invoke_without_command=True)
    async def addtorole(self, ctx: _Context, role_to_add: _Role, required_role: _Role, *, required_roles: str = None) -> None:
        """
        Add a Role to all members with the specified roles.

        Usage:
          vivi role addtorole [role to add] [required role 1] <required role 2 and more>

        Parameters:
          role_to_add: Mandatory. An ID or a mention of a Role on this server.
          required_role: Mandatory. An ID or a mention of a Role on this server that is required.
          required_roles: Optional. IDs or mentions of further required roles.

        Examples:
          vivi role addtorole @foo @bar - Adds the role @foo to all members with the @bar role.
          vivi role addtorole @foo @bar @baz - Adds the role @foo to all members having the roles @bar and @baz.
        """
        _utils.assert_.authorized_channel_or_server_manager(ctx, _bot_settings.AUTHORIZED_CHANNEL_IDS)

        if role_to_add.position >= ctx.me.top_role.position:
            raise Exception(f'Cannot add the role {role_to_add.mention}: it is either my top role or above.')

        roles = [required_role]
        if required_roles:
            for role_id_or_mention in required_roles.split(' '):
                roles.append(ctx.guild.get_role(role_id_or_mention))
        members = None
        for role in roles:
            if members is None:
                members = role.members
            else:
                members = list(set(members).intersection(role.members))
        
        reason = f'User {ctx.author.display_name} (ID: {ctx.author.id}) issued command: role addtorole'
        confirmator = _utils.Confirmator(ctx, f'This command will add the role `{role_to_add}` to {len(members)} members!')
        if (await confirmator.wait_for_option_selection()):
            for member in members:
                await member.add_roles(role_to_add, reason=reason)

            lines = [
                'The command completed successfully.',
                f'Added role {role} to {len(members)} members:',
                *members
            ]
            await _utils.discord.reply_lines(ctx, lines)


    @_bot_has_guild_permissions(manage_roles=True)
    @_has_guild_permissions(manage_roles=True)
    @role.group(name='clear', brief='Remove a role from all members', invoke_without_command=True)
    async def clear(self, ctx: _Context, role_id_or_mention: _Role) -> None:
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
        if ctx.invoked_subcommand is None:
            _utils.assert_.authorized_channel_or_server_manager(ctx, _bot_settings.AUTHORIZED_CHANNEL_IDS)

            if role_id_or_mention.position >= ctx.me.top_role.position:
                raise Exception(f'Cannot remove the role {role_id_or_mention.mention}: it is either my top role or above.')

            reason = f'User {ctx.author.display_name} (ID: {ctx.author.id}) issued command: role clear'
            members = list(role_id_or_mention.members)
            if len(members) > 0:
                confirmator = _utils.Confirmator(ctx, f'This command will remove the role `{role_id_or_mention}` from {len(members)} members!')
                if (await confirmator.wait_for_option_selection()):
                    users_removed = []
                    for member in members:
                        try:
                            await member.remove_roles(role_id_or_mention, reason=reason)
                            users_removed.append(f'{member.display_name} ({member.id})')
                        except:
                            pass
                    lines = [
                        'The command completed successfully.',
                        f'Removed role {role_id_or_mention} from members:',
                        *sorted(users_removed)
                    ]
                    await _utils.discord.reply_lines(ctx, lines)
            else:
                await _utils.discord.reply(ctx, f'There are no members with the role {role_id_or_mention}.')


    @_bot_has_guild_permissions(manage_roles=True)
    @_has_guild_permissions(manage_roles=True)
    @clear.command(name='users', brief='Remove all roles from specified members')
    async def clear_users(self, ctx: _Context, *, user_ids: str) -> None:
        """
        Remove all Roles from multiple members of this server.

        Usage:
          vivi role clear users [user_id 1] <user_id 2> <user_id ...>

        Parameters:
          user_id(s): Mandatory. One or more User IDs of members of this server.

        Examples:
          vivi role clear users 1 2 3 - Removes all Roles from the members with ids 1, 2 & 3.
        """
        _utils.assert_.authorized_channel_or_server_manager(ctx, _bot_settings.AUTHORIZED_CHANNEL_IDS)
        user_ids = set(user_ids.split(' '))
        reason = f'User {ctx.author.display_name} (ID: {ctx.author.id}) issued command: role clear users'
        confirmator = _utils.Confirmator(ctx, f'This command will remove all non-managed roles from {len(user_ids)} members!\nNote: Roles that are above my highest role will not be removed.')
        if (await confirmator.wait_for_option_selection()):
            users_removed = []
            not_removed = []
            for user_id in user_ids:
                member: _Member = ctx.guild.get_member(int(user_id))
                if member:
                    roles = [role for role in member.roles if role.position and role.position < ctx.me.top_role.position and not role.managed]
                    await member.remove_roles(*roles, reason=reason)
                    users_removed.append(f'{member.display_name} ({user_id})')
                else:
                    not_removed.append(user_id)

            lines = ['The command completed successfully.']
            if users_removed:
                lines.extend((
                    f'Removed all roles from {len(users_removed)} members:',
                    *users_removed
                ))
            if not_removed:
                lines.extend((
                    f'Could not remove roles from {len(not_removed)} users with ID:',
                    *not_removed
                ))
            await _utils.discord.reply_lines(ctx, lines)


    @_bot_has_guild_permissions(manage_roles=True)
    @_has_guild_permissions(manage_roles=True)
    @role.command(name='remove', brief='Remove a role from specified members')
    async def remove(self, ctx: _Context, role_id_or_mention: _Role, *, user_ids: str) -> None:
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
        _utils.assert_.authorized_channel_or_server_manager(ctx, _bot_settings.AUTHORIZED_CHANNEL_IDS)

        if role_id_or_mention.position >= ctx.me.top_role.position:
            raise Exception(f'Cannot remove the role {role_id_or_mention.mention}: it is either my top role or above.')

        user_ids = set(user_ids.split(' '))
        reason = f'User {ctx.author.display_name} (ID: {ctx.author.id}) issued command: role remove'
        confirmator = _utils.Confirmator(ctx, f'This command removes the role `{role_id_or_mention}` from {len(user_ids)} members.')
        if (await confirmator.wait_for_option_selection()):
            users_removed = []
            not_removed = []
            for user_id in user_ids:
                member = ctx.guild.get_member(int(user_id))
                if member:
                    await member.remove_roles(role_id_or_mention, reason=reason)
                    users_removed.append(f'{member.display_name} ({user_id})')
                else:
                    not_removed.append(user_id)

            lines = ['The command completed successfully.']
            if users_removed:
                lines.extend((
                    f'Removed role {role_id_or_mention} from {len(users_removed)} members:',
                    *users_removed
                ))
            if not_removed:
                lines.extend((
                    f'Could not remove role from {len(not_removed)} users with ID:',
                    *not_removed
                ))
            await _utils.discord.reply_lines(ctx, lines)
    

    @_bot_has_guild_permissions(manage_roles=True)
    @_has_guild_permissions(manage_roles=True)
    @role.group(name='removefromrole', brief='Remove a Role from members with certain role(s)', invoke_without_command=True)
    async def removefromrole(self, ctx: _Context, role_to_clear: _Role, required_role: _Role, *, required_roles: str = None) -> None:
        """
        Remove a Role from all members with the specified roles.

        Usage:
          vivi role removefromrole [role to add] [required role 1] <required role 2 and more>

        Parameters:
          role_to_clear: Mandatory. An ID or a mention of a Role on this server.
          required_role: Mandatory. An ID or a mention of a Role on this server that is required.
          required_roles: Optional. IDs or mentions of further required roles.

        Examples:
          vivi role removefromrole @foo @bar - Clears the role @foo from all members with the @bar role.
          vivi role removefromrole @foo @bar @baz - Clears the role @foo from all members having the roles @bar and @baz.
        """
        _utils.assert_.authorized_channel_or_server_manager(ctx, _bot_settings.AUTHORIZED_CHANNEL_IDS)

        if role_to_clear.position >= ctx.me.top_role.position:
            raise Exception(f'Cannot add the role {role_to_clear.mention}: it is either my top role or above.')

        roles = [required_role]
        if required_roles:
            for role_id_or_mention in required_roles.split(' '):
                roles.append(ctx.guild.get_role(role_id_or_mention))
        members = None
        for role in roles:
            if members is None:
                members = role.members
            else:
                members = list(set(members).intersection(role.members))
        
        reason = f'User {ctx.author.display_name} (ID: {ctx.author.id}) issued command: role addtorole'
        confirmator = _utils.Confirmator(ctx, f'This command will remove the role `{role_to_clear}` from {len(members)} members!')
        if (await confirmator.wait_for_option_selection()):
            for member in members:
                await member.remove_roles(role_to_clear, reason=reason)

            lines = [
                'The command completed successfully.',
                f'Removed role {role} from {len(members)} members:',
                *members
            ]
            await _utils.discord.reply_lines(ctx, lines)


def setup(bot: _Bot):
    bot.add_cog(RoleManagement(bot))