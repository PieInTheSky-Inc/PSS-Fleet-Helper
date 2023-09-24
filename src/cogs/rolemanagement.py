from typing import List as _List
from typing import Union as _Union

import discord as _discord
import discord.ext.commands as _commands

from .cog_base import CogBase as _CogBase
from .. import bot_settings as _bot_settings
from .. import utils as _utils
from .. import model as _model



class RoleManagement(_CogBase):
    PRINT_PROGRESS_EVERY_X_MEMBERS: int = 10

    @_commands.group(name='role', aliases=['roles'], brief='Role management', invoke_without_command=True)
    async def role(self, ctx: _commands.Context) -> None:
        if ctx.invoked_subcommand is None:
            _utils.assert_.authorized_channel_or_server_manager(ctx, _bot_settings.AUTHORIZED_CHANNEL_IDS)
            await ctx.send_help('role')


    @_commands.bot_has_guild_permissions(manage_roles=True)
    @_commands.has_guild_permissions(manage_roles=True)
    @role.command(name='add', brief='Add Role to members')
    async def add(self, ctx: _commands.Context, role_to_add: _discord.Role, *, user_ids: str) -> None:
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
        _utils.assert_.can_add_remove_role(ctx.me, role_to_add, 'add')

        user_ids = set(user_ids.split(' '))
        if user_ids:
            reason = f'User {ctx.author.display_name} (ID: {ctx.author.id}) issued command: role add'
            confirmator = _utils.Confirmator(ctx, f'This command will add the role `{role_to_add}` to {len(user_ids)} members.')

            if (await confirmator.wait_for_option_selection()):
                users_added = []
                users_not_added = []
                reply = (await _utils.discord.reply_lines(ctx, [f'Adding role. Progress: 0/{len(user_ids)} members']))[0]

                for i, user_id in enumerate(user_ids):
                    member = ctx.guild.get_member(int(user_id))
                    if member:
                        if role_to_add not in member.roles:
                            try:
                                await member.add_roles(role_to_add, reason=reason)
                                users_added.append(f'{member.display_name} ({user_id})')
                            except:
                                users_not_added.append(f'{member.display_name} ({user_id})')
                        else:
                            users_added.append(f'{member.display_name} ({user_id})')
                    else:
                        users_not_added.append(user_id)

                    if i and self.__print_progress(i):
                        _utils.discord.edit_lines(reply, [f'Adding role. Progress: {i}/{len(user_ids)} members'])

                lines = [
                    'The command completed successfully.',
                    f'Added role {role_to_add} to {len(users_added)} members:',
                    *users_added
                ]
                if users_not_added:
                    lines.append(f'Could not add role to {len(users_not_added)} users with ID:')
                    lines.extend(users_not_added)

                if not _utils.discord.fits_single_message(lines):
                    lines = [
                        'The command completed successfully.',
                        f'Added role {role_to_add} to {len(users_added)} members.',
                    ]
                    if users_not_added:
                        lines.append(f'Could not add role to {len(users_not_added)} members.')
                
                await _utils.discord.edit_lines(reply, lines)
    

    @_commands.bot_has_guild_permissions(manage_roles=True)
    @_commands.has_guild_permissions(manage_roles=True)
    @role.group(name='addtorole', brief='Add Role to members with certain role(s)', invoke_without_command=True)
    async def addtorole(self, ctx: _commands.Context, role_to_add: _discord.Role, required_role: _discord.Role, *, required_roles: str = None) -> None:
        """
        Add a Role to all members with all of the specified roles.

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
        _utils.assert_.can_add_remove_role(ctx.me, role_to_add, 'add')

        roles = [required_role]
        if required_roles:
            roles.extend(ctx.guild.get_role(role_id_or_mention) for role_id_or_mention in required_roles.split(' '))
                
        members_with_role_to_add = set(role_to_add.members)
        members_with_required_roles = set(self.__get_members_with_roles(ctx, *roles))
        members = list(members_with_required_roles.difference(members_with_role_to_add))
        
        if members:
            reason = f'User {ctx.author.display_name} (ID: {ctx.author.id}) issued command: role addtorole'
            confirmator = _utils.Confirmator(ctx, f'This command will add the role `{role_to_add}` to {len(members)} members.')

            if (await confirmator.wait_for_option_selection()):
                members_added_count = 0
                reply = (await _utils.discord.reply_lines(ctx, [f'Adding role. Progress: 0/{len(members)} members']))[0]

                for i, member in enumerate(members):
                    try:
                        await member.add_roles(role_to_add, reason=reason)
                        members_added_count += 1
                    except:
                        pass

                    if i and self.__print_progress(i):
                        await _utils.discord.edit_lines(reply, [f'Adding role. Progress: {i}/{len(members)} members'])

                lines = [
                    'The command completed successfully.',
                    f'Added role {role_to_add} to {members_added_count} members.',
                ]
                if members_added_count < len(members):
                    lines.append(f'Could not add role {role_to_add} to {len(members) - members_added_count} members.')

                await _utils.discord.edit_lines(reply, lines)


    @_commands.bot_has_guild_permissions(manage_roles=True)
    @_commands.has_guild_permissions(manage_roles=True)
    @role.group(name='clear', brief='Remove a role from all members', invoke_without_command=True)
    async def clear(self, ctx: _commands.Context, role_to_remove: _discord.Role) -> None:
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
            _utils.assert_.can_add_remove_role(ctx.me, role_to_remove, 'clear')

            members = list(role_to_remove.members)

            if members:
                reason = f'User {ctx.author.display_name} (ID: {ctx.author.id}) issued command: role clear'
                confirmator = _utils.Confirmator(ctx, f'This command will remove the role `{role_to_remove}` from {len(members)} members.')

                if (await confirmator.wait_for_option_selection()):
                    users_cleared = []
                    users_not_cleared = []
                    reply = (await _utils.discord.reply_lines(ctx, [f'Clearing role. Progress: 0/{len(members)} members']))[0]

                    for i, member in enumerate(members):
                        try:
                            await member.remove_roles(role_to_remove, reason=reason)
                            users_cleared.append(f'{member.display_name} ({member.id})')
                        except:
                            users_not_cleared.append(f'{member.display_name} ({member.id})')

                        if i and self.__print_progress(i):
                            await _utils.discord.edit_lines(reply, [f'Clearing role. Progress: {i}/{len(members)} members'])

                    lines = [
                        'The command completed successfully.',
                        f'Cleared role {role_to_remove} from {len(users_cleared)} members:',
                        *sorted(users_cleared)
                    ]
                    if users_not_cleared:
                        lines.append(f'Could not clear role {role_to_remove} from {len(users_cleared)} members:')
                        lines.extend(users_not_cleared)

                    if not _utils.discord.fits_single_message(lines):
                        lines = [
                            'The command completed successfully.',
                            f'Cleared role {role_to_remove} from {len(users_cleared)} members.',
                        ]
                        if len(users_cleared) < len(members):
                            lines.append(f'Could not clear role {role_to_remove} from {len(members) - len(users_cleared)} members.')
                    
                    await _utils.discord.edit_lines(reply, lines)
            else:
                await _utils.discord.reply(ctx, f'There are no members with the role {role_to_remove}.')


    @_commands.bot_has_guild_permissions(manage_roles=True)
    @_commands.has_guild_permissions(manage_roles=True)
    @clear.command(name='users', brief='Remove all roles from specified members')
    async def clear_users(self, ctx: _commands.Context, *, user_ids: str) -> None:
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

        if user_ids:
            reason = f'User {ctx.author.display_name} (ID: {ctx.author.id}) issued command: role clear users'
            confirmator = _utils.Confirmator(ctx, f'This command will remove all non-managed roles from {len(user_ids)} members.\nNote: Roles that are above my highest role will not be removed.')

            if (await confirmator.wait_for_option_selection()):
                users_removed = []
                users_not_removed = []
                reply = (await _utils.discord.reply_lines(ctx, [f'Clearing roles. Progress: 0/{len(user_ids)} members']))[0]

                for i, user_id in enumerate(user_ids):
                    member: _discord.Member = ctx.guild.get_member(int(user_id))
                    if member:
                        roles = [role for role in member.roles if role.position and role.position < ctx.me.top_role.position and not role.managed]
                        try:
                            await member.remove_roles(*roles, reason=reason)
                            users_removed.append(f'{member.display_name} ({user_id})')
                        except:
                            users_not_removed.append(f'{member.display_name} ({user_id})')
                    else:
                        users_not_removed.append(user_id)

                    if i and self.__print_progress(i):
                        await _utils.discord.edit_lines(reply, [f'Clearing roles. Progress: {i}/{len(user_ids)} members'])

                lines = ['The command completed successfully.']
                if users_removed:
                    lines.extend((
                        f'Removed all roles from {len(users_removed)} members:',
                        *users_removed
                    ))
                if users_not_removed:
                    lines.extend((
                        f'Could not remove roles from {len(users_not_removed)} users with ID:',
                        *users_not_removed
                    ))

                if not _utils.discord.fits_single_message(lines):
                    lines = [
                        'The command completed successfully.',
                        f'Removed all roles from {len(users_removed)} members.',
                        f'Could not remove all roles from {len(users_not_removed)} users.',
                    ]
                    
                await _utils.discord.edit_lines(reply, lines)


    @_commands.bot_has_guild_permissions(manage_roles=True)
    @_commands.has_guild_permissions(manage_roles=True)
    @role.command(name='remove', brief='Remove a role from specified members')
    async def remove(self, ctx: _commands.Context, role_to_remove: _discord.Role, *, user_ids: str) -> None:
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
        _utils.assert_.can_add_remove_role(ctx.me, role_to_remove, 'remove')

        user_ids = set(user_ids.split(' '))

        if user_ids:
            reason = f'User {ctx.author.display_name} (ID: {ctx.author.id}) issued command: role remove'
            confirmator = _utils.Confirmator(ctx, f'This command removes the role `{role_to_remove}` from {len(user_ids)} members.')

            if (await confirmator.wait_for_option_selection()):
                users_removed = []
                users_not_removed = []
                reply = (await _utils.discord.reply_lines(ctx, [f'Removing role. Progress: 0/{len(user_ids)} members']))[0]

                for i, user_id in enumerate(user_ids):
                    member = ctx.guild.get_member(int(user_id))
                    if member:
                        if role_to_remove in member.roles:
                            try:
                                await member.remove_roles(role_to_remove, reason=reason)
                                users_removed.append(f'{member.display_name} ({user_id})')
                            except:
                                users_not_removed.append(f'{member.display_name} ({user_id})')
                        else:
                            users_removed.append(f'{member.display_name} ({user_id})')
                    else:
                        users_not_removed.append(user_id)

                    if i and self.__print_progress(i):
                        await _utils.discord.edit_lines(reply, [f'Removing role. Progress: {i}/{len(user_ids)} members'])

                lines = [
                    'The command completed successfully.',
                    f'Removed role {role_to_remove} from {len(users_removed)} members:',
                    *users_removed
                ]
                if users_not_removed:
                    lines.extend((
                        f'Could not remove role from {len(users_not_removed)} users with ID:',
                        *users_not_removed
                    ))

                if not _utils.discord.fits_single_message(lines):
                    lines = [
                        'The command completed successfully.',
                        f'Removed role {role_to_remove} from {len(users_removed)} members.',
                    ]
                    if users_not_removed:
                        lines.append(f'Could not remove role from {len(users_not_removed)} users.')
                    
                await _utils.discord.edit_lines(reply, lines)
    

    @_commands.bot_has_guild_permissions(manage_roles=True)
    @_commands.has_guild_permissions(manage_roles=True)
    @role.group(name='removefromrole', brief='Remove a Role from members with certain role(s)', invoke_without_command=True)
    async def removefromrole(self, ctx: _commands.Context, role_to_remove: _discord.Role, required_role: _discord.Role, *, required_roles: str = None) -> None:
        """
        Remove a Role from all members with all of the specified roles.

        Usage:
          vivi role removefromrole [role to remove] [required role 1] <required role 2 and more>

        Parameters:
          role_to_remove: Mandatory. An ID or a mention of a Role on this server.
          required_role: Mandatory. An ID or a mention of a Role on this server that is required.
          required_roles: Optional. IDs or mentions of further required roles.

        Examples:
          vivi role removefromrole @foo @bar - Clears the role @foo from all members with the @bar role.
          vivi role removefromrole @foo @bar @baz - Clears the role @foo from all members having the roles @bar and @baz.
        """
        _utils.assert_.authorized_channel_or_server_manager(ctx, _bot_settings.AUTHORIZED_CHANNEL_IDS)
        _utils.assert_.can_add_remove_role(ctx.me, role_to_remove, 'remove')

        roles = [required_role]
        if required_roles:
            roles.extend(ctx.guild.get_role(role_id_or_mention) for role_id_or_mention in required_roles.split(' '))

        members = self.__get_members_with_roles(ctx, role_to_remove, *roles)

        if members:
            reason = f'User {ctx.author.display_name} (ID: {ctx.author.id}) issued command: role removefromrole'
            confirmator = _utils.Confirmator(ctx, f'This command will remove the role `{role_to_remove}` from {len(members)} members.')

            if (await confirmator.wait_for_option_selection()):
                users_removed_count = 0
                reply = (await _utils.discord.reply_lines(ctx, [f'Removing role. Progress: 0/{len(members)} members']))[0]

                for i, member in enumerate(members):
                    try:
                        await member.remove_roles(role_to_remove, reason=reason)
                        users_removed_count += 1
                    except:
                        pass

                    if i and self.__print_progress(i):
                        await _utils.discord.edit_lines(reply, [f'Removing role. Progress: {i}/{len(members)} members'])

                lines = [
                    'The command completed successfully.',
                    f'Removed role {role_to_remove} from {users_removed_count} members.',
                ]
                if users_removed_count < len(members):
                    lines.append(f'Could not remove role {role_to_remove} from {len(members) - users_removed_count} members.')

                await _utils.discord.edit_lines(reply, lines)
        else:
            await _utils.discord.reply(ctx, f'There are no members with the role to be removed matching the criteria.')
    




    def __print_progress(self, current_count: int) -> bool:
        return not (current_count % RoleManagement.PRINT_PROGRESS_EVERY_X_MEMBERS)
    

    def __get_members_with_roles(self, ctx: _commands.Context, *roles: _List[_Union[int, _discord.Role]]) -> _List[_discord.Member]:
        all_roles: _List[_discord.Role] = []
        for role in roles:
            if isinstance(role, _discord.Role):
                all_roles.append(role)
            elif isinstance(role, int):
                all_roles.append(ctx.guild.get_role(role))

        if not all_roles:
            return []

        result = set(all_roles[0].members)
        for role in all_roles[1:]:
            result = result.intersection(role.members)
        
        return list(result)


def setup(bot: _model.PssApiDiscordBot):
    bot.add_cog(RoleManagement(bot))