import json as _json
from typing import Callable as _Callable
from typing import List as _List
from typing import Optional as _Optional
from typing import Tuple as _Tuple

import discord as _discord
import discord.ext.commands as _commands

from .cog_base import CogBase as _CogBase
from .. import bot_settings as _bot_settings
from .. import utils as _utils
from .. import converters as _converters
from .. import model as _model



# ---------- Constants ----------



# ---------- Cog ----------

class ReactionRoles(_CogBase):
    """
    Commands for configuring Reaction Roles on this server.
    """

    @_CogBase.listener()
    async def on_raw_reaction_add(self, payload: _discord.RawReactionActionEvent) -> None:
        if payload.member.guild.me == payload.member:
            return

        with _model.orm.create_session() as session:
            reaction_roles: _List[_model.ReactionRole] = _model.orm.get_all_filtered_by(
                _model.ReactionRole,
                session,
                guild_id=payload.member.guild.id,
                is_active=True,
                message_id=payload.message_id
            )
        member_roles_ids = [role.id for role in payload.member.roles]
        for reaction_role in reaction_roles:
            emoji_match = reaction_role.reaction == payload.emoji.name or reaction_role.reaction == f'<:{payload.emoji.name}:{payload.emoji.id}>'
            if emoji_match:
                member_meets_requirements = all(requirement.role_id in member_roles_ids for requirement in reaction_role.role_requirements)
                if member_meets_requirements:
                    await reaction_role.apply_add(payload.member)


    @_CogBase.listener()
    async def on_raw_reaction_remove(self, payload: _discord.RawReactionActionEvent) -> None:
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        member = guild.get_member(payload.user_id)
        if not member or member == guild.me:
            return

        with _model.orm.create_session() as session:
            reaction_roles: _List[_model.ReactionRole] = _model.orm.get_all_filtered_by(
                _model.ReactionRole,
                session,
                guild_id=payload.guild_id,
                is_active=True,
                message_id=payload.message_id
            )
        member_roles_ids = [role.id for role in member.roles]
        for reaction_role in reaction_roles:
            emoji_match = reaction_role.reaction == payload.emoji.name or reaction_role.reaction == f'<:{payload.emoji.name}:{payload.emoji.id}>'
            if emoji_match:
                member_meets_requirements = all(requirement.role_id in member_roles_ids for requirement in reaction_role.role_requirements)
                if member_meets_requirements:
                    await reaction_role.apply_remove(member)


    @_commands.guild_only()
    @_commands.group(name='reactionrole', aliases=['rr'], brief='Set up reaction roles', invoke_without_command=True)
    async def base(self, ctx: _commands.Context) -> None:
        """
        Set up cool Reaction Roles for this server. Check out the subcommands.
        """
        if ctx.invoked_subcommand is None:
            _utils.assert_.authorized_channel_or_server_manager(ctx, _bot_settings.AUTHORIZED_CHANNEL_IDS)
            await ctx.send_help('reactionrole')


    @_commands.guild_only()
    @_commands.bot_has_guild_permissions(manage_roles=True)
    @_commands.has_guild_permissions(manage_roles=True)
    @base.group(name='activate', aliases=['enable', 'on'], brief='Activate a Reaction Role', invoke_without_command=True)
    async def activate(self, ctx: _commands.Context, reaction_role_id: int) -> None:
        """
        Attempts to activate the deactivated Reaction Role with the given ID on this server. This means adding the specified reaction to the specified channel and listening for members adding or removing said reaction to perform the configured role changes.
        Reaction Role IDs can be retrieved via the command: vivi reactionrole list

        Usage:
          vivi reactionrole activate [reaction_role_id]

        Parameters:
          reaction_role_id: Mandatory. The ID of an inactive Reaction Role on this server.

        Usage:
          vivi reactionrole activate 1 - Attempts to activate the Reaction Role with the ID 1.
        """
        _utils.assert_.authorized_channel_or_server_manager(ctx, _bot_settings.AUTHORIZED_CHANNEL_IDS)
        success = False
        with _model.orm.create_session() as session:
            reaction_role = _model.orm.get_first_filtered_by(
                _model.ReactionRole,
                session,
                id=reaction_role_id,
                guild_id=ctx.guild.id
            )
        if reaction_role:
            if reaction_role.is_active:
                raise Exception(f'The Reaction Role {reaction_role} is already active.')
            success = await reaction_role.try_activate(ctx)
            if success:
                with _model.orm.create_session() as session:
                    reaction_role = _model.orm.merge(session, reaction_role)
                    reaction_role.save(session)
            else:
                raise Exception(f'Failed to activate Reaction Role {reaction_role}.')
        else:
            raise Exception(f'There is no Reaction Role configured on this server having the ID `{reaction_role_id}`.')
        await _utils.discord.reply(ctx, f'Activated Reaction Role {reaction_role}.')


    @_commands.guild_only()
    @_commands.bot_has_guild_permissions(manage_roles=True)
    @_commands.has_guild_permissions(manage_roles=True)
    @activate.command(name='all', brief='Activate all Reaction Roles')
    async def activate_all(self, ctx: _commands.Context) -> None:
        """
        Attempts to activate all inactive Reaction Roles configured on this server. This means adding the specified reaction to the specified channel and listening for members adding or removing said reaction to perform the configured role changes. Will print any Reaction Role that could not be activated.

        Usage:
          vivi reactionrole activate all
        """
        _utils.assert_.authorized_channel_or_server_manager(ctx, _bot_settings.AUTHORIZED_CHANNEL_IDS)
        reaction_roles: _List[_model.ReactionRole] = []
        succeeded: _List[_model.ReactionRole] = []
        failed: _List[_model.ReactionRole] = []
        with _model.orm.create_session() as session:
            reaction_roles = _model.orm.get_all_filtered_by(
                _model.ReactionRole,
                session,
                guild_id=ctx.guild.id,
                is_active=False,
            )
            if reaction_roles:
                for reaction_role in reaction_roles:
                    if (await reaction_role.try_activate(ctx)):
                        succeeded.append(reaction_role)
                    else:
                        failed.append(reaction_role)
            else:
                raise Exception(f'There are no Reaction Roles configured on this server.')
        if succeeded:
            with _model.orm.create_session() as session:
                for reaction_role in succeeded:
                    _model.orm.merge(session, reaction_role)
            session.commit()
        response_lines = [f'Activated {len(succeeded)} of {len(reaction_roles)} Reaction Roles on this server.']
        if failed:
            response_lines.append('Could not activate the following roles:')
            for failed_reaction_role in failed:
                response_lines.append(f'ID: {failed_reaction_role.id} - Name: {failed_reaction_role.name}')
        await _utils.discord.reply_lines(ctx, response_lines)


    @_commands.guild_only()
    @_commands.bot_has_guild_permissions(manage_roles=True)
    @_commands.has_guild_permissions(manage_roles=True)
    @base.command(name='add', brief='Add a reaction role')
    async def add(self, ctx: _commands.Context, emoji: str = None, message_link: str = None, *, name: str = None) -> None:
        """
        Add a new Reaction Role to this server. Starts an assistant guiding through the creation process.

        Usage:
          vivi reactionrole add
        """
        _utils.assert_.authorized_channel_or_server_manager(ctx, _bot_settings.AUTHORIZED_CHANNEL_IDS)
        abort_text = 'Aborted. No reaction role has been created.'

        welcome_lines = [
                '```Welcome to the Reaction Role assistent.',
                'A Reaction Role can be created in 3 steps:',
                '- The basic definition',
                '- Role Changes - Configure which roles should be added/removed',
                '- Role Requirements - Configure which roles will be required to activate the Reaction Role',
                '',
                'You\'ll be guided step by step.```',
                '_ _',
            ]
        await _utils.discord.reply_lines(ctx, welcome_lines, mention_author=True)

        name: str = name or None
        emoji: str = emoji or None
        channel_id: int = None
        message_id: int = None
        details, aborted = await inquire_for_reaction_role_details(ctx, abort_text, name=name, emoji=emoji, message_link=message_link)
        if aborted:
            return
        if details:
            name, emoji, channel_id, message_id = details

        # role, add, allow_toggle, channel, message
        role_reaction_changes: _List[_Tuple[_discord.Role, bool, bool, _discord.TextChannel, str]] = []
        # role
        role_reaction_requirements: _List[_discord.Role] = []

        add_role_change = True
        while add_role_change:
            role_reaction_change, aborted = await inquire_for_role_change_details(ctx, abort_text)
            if aborted:
                return
            role_reaction_changes.append(role_reaction_change)

            add_role_change, aborted, _ = await _utils.discord.inquire_for_true_false(ctx, 'Do you want to add another Role Change?', abort_text=abort_text)
            if aborted:
                return

        add_role_requirement, aborted, _ = await _utils.discord.inquire_for_true_false(ctx, 'Do you want to add a Role Requirement\n(A role required to trigger this Reaction Role)?', abort_text=abort_text)
        if aborted:
            return

        while add_role_requirement:
            role_id, aborted = await inquire_for_role_requirement_add(ctx, abort_text)
            if aborted:
                return
            role_reaction_requirements.append(role_id)

            add_role_requirement, aborted, _ = await _utils.discord.inquire_for_true_false(ctx, 'Do you want to add another Role Requirement?', abort_text=abort_text)
            if aborted:
                return

        confirmation_prompt_lines = ['**Creating a new Reaction Role**',
            f'Name = {name}',
            f'Message ID = {message_id} ({_utils.discord.create_discord_link(ctx.guild.id, channel_id, message_id)})',
            f'Emoji = {emoji}',
        ]
        if role_reaction_requirements:
            required_roles = [ctx.guild.get_role(role_id) for role_id in role_reaction_requirements]
            required_roles_text = ', '.join([role.name for role in required_roles if role])
            confirmation_prompt_lines.append(f'Required role(s) = {required_roles_text}')
        confirmation_prompt_lines.append(f'_discord.Role Changes_')
        review_messages = []
        for i, (role_id, add, allow_toggle, message_text, message_channel_id, message_embed) in enumerate(role_reaction_changes, 1):
            role: _discord.Role = ctx.guild.get_role(role_id)
            add_text = 'add' if add else 'remove'
            send_message_str = ''
            if message_channel_id:
                message_channel: _discord.TextChannel = ctx.guild.get_channel(message_channel_id)
                send_message_str = f' and send a message to {message_channel.mention} (review message text below)'
                review_messages.append((i, message_text))
            confirmation_prompt_lines.append(f'{i} = {add_text} role `{role.name}`{send_message_str}')
        prompts: _List[_discord.Message] = await _utils.discord.reply_lines(ctx, confirmation_prompt_lines)
        for role_change_number, msg in review_messages:
            prompts.append((await prompts[0].reply(f'__**Message for Role Change \#{role_change_number}**__\n{msg}', mention_author=False)))

        finish_setup = await _utils.discord.inquire_for_true_false(ctx, 'Do you want to set up the Reaction Role? (selecting \'no\' will abort the process.)')
        if not finish_setup:
            await _utils.discord.reply(ctx, abort_text)
            return

        with _model.orm.create_session() as session:
            reaction_role = _model.ReactionRole.make(ctx.guild.id, channel_id, message_id, name, emoji)
            reaction_role.create(session, commit=False)
            for role_reaction_change_def in role_reaction_changes:
                role_change = reaction_role.add_change(*role_reaction_change_def)
                role_change.create(session, commit=False)
            for role_id in role_reaction_requirements:
                role_requirement = reaction_role.add_requirement(role_id)
                role_requirement.create(session, commit=False)
            reaction_role.save(session)

        activate, _, _ = await _utils.discord.inquire_for_true_false(ctx, f'Created Reaction Role {reaction_role}.\nDo you want to activate it now?')
        if activate:
            cmd = self.bot.get_command('reactionrole activate')
            await ctx.invoke(cmd, reaction_role_id=reaction_role.id)


    @_commands.guild_only()
    @_commands.bot_has_guild_permissions(manage_roles=True)
    @_commands.has_guild_permissions(manage_roles=True)
    @base.group(name='deactivate', aliases=['disable', 'off'], brief='Deactivate a Reaction Role', invoke_without_command=True)
    async def deactivate(self, ctx: _commands.Context, reaction_role_id: int) -> None:
        """
        Attempts to deactivate the activated Reaction Role with the given ID on this server. This means removing the specified reaction to the specified channel and no more listening for members adding or removing said reaction.
        Reaction Role IDs can be retrieved via the command: vivi reactionrole list

        Usage:
          vivi reactionrole deactivate [reaction_role_id]

        Parameters:
          reaction_role_id: Mandatory. The ID of an active Reaction Role on this server.

        Usage:
          vivi reactionrole deactivate 1 - Attempts to deactivate the Reaction Role with the ID 1.
        """
        _utils.assert_.authorized_channel_or_server_manager(ctx, _bot_settings.AUTHORIZED_CHANNEL_IDS)
        with _model.orm.create_session() as session:
            reaction_role = _model.orm.get_first_filtered_by(
                _model.ReactionRole,
                session,
                id=reaction_role_id,
                guild_id=ctx.guild.id
            )
        if reaction_role:
            if not reaction_role.is_active:
                raise Exception(f'The Reaction Role {reaction_role} is already inactive.')
            if (await reaction_role.try_deactivate(ctx)):
                with _model.orm.create_session() as session:
                    reaction_role = _model.orm.merge(session, reaction_role)
                    reaction_role.save(session)
            else:
                raise Exception(f'Failed to deactivate Reaction Role {reaction_role}.')
        else:
            raise Exception(f'There is no Reaction Role configured on this server having the ID `{reaction_role_id}`.')
        await _utils.discord.reply(ctx, f'Deactivated Reaction Role {reaction_role}.')


    @_commands.guild_only()
    @_commands.bot_has_guild_permissions(manage_roles=True)
    @_commands.has_guild_permissions(manage_roles=True)
    @deactivate.command(name='all', brief='Deactivate all Reaction Roles')
    async def deactivate_all(self, ctx: _commands.Context) -> None:
        """
        Attempts to deactivate all active Reaction Roles configured on this server. This means removing the specified reaction to the specified channel and no more listening for members adding or removing said reaction. Will print any Reaction Role that could not be activated.

        Usage:
          vivi reactionrole deactivate all
        """
        _utils.assert_.authorized_channel_or_server_manager(ctx, _bot_settings.AUTHORIZED_CHANNEL_IDS)
        succeeded: _List[_model.ReactionRole] = []
        failed: _List[_model.ReactionRole] = []
        with _model.orm.create_session() as session:
            reaction_roles = _model.orm.get_all_filtered_by(
                _model.ReactionRole,
                session,
                guild_id=ctx.guild.id
            )
        if reaction_roles:
            for reaction_role in reaction_roles:
                if (await reaction_role.try_deactivate(ctx)):
                    succeeded.append(reaction_role)
                else:
                    failed.append(reaction_role)
        else:
            raise Exception(f'There are no Reaction Roles configured on this server.')
        if succeeded:
            with _model.orm.create_session() as session:
                for reaction_role in succeeded:
                    _model.orm.merge(session, reaction_role)
                session.commit()
        response_lines = [f'Deactivated {len(succeeded)} of {len(reaction_roles)} Reaction Roles on this server.']
        if failed:
            response_lines.append('Could not deactivate the following roles:')
            for failed_reaction_role in failed:
                response_lines.append(f'ID: {failed_reaction_role.id} - Name: {failed_reaction_role.name}')
        await _utils.discord.reply_lines(ctx, response_lines)


    @_commands.guild_only()
    @_commands.bot_has_guild_permissions(manage_roles=True)
    @_commands.has_guild_permissions(manage_roles=True)
    @base.group(name='delete', aliases=['remove'], brief='Delete a Reaction Role')
    async def delete(self, ctx: _commands.Context, reaction_role_id: int) -> None:
        """
        Deletes an inactive Reaction Role with the given ID on this server.
        Reaction Role IDs can be retrieved via the command: vivi reactionrole list

        Usage:
          vivi reactionrole delete [reaction_role_id]

        Parameters:
          reaction_role_id: Mandatory. The ID of an inactive Reaction Role on this server.

        Examples:
          vivi reactionrole delete 1 - Attempts to delete the Reaction Role with the ID 1
        """
        _utils.assert_.authorized_channel_or_server_manager(ctx, _bot_settings.AUTHORIZED_CHANNEL_IDS)
        with _model.orm.create_session() as session:
            reaction_role = _model.orm.get_first_filtered_by(
                _model.ReactionRole,
                session,
                id=reaction_role_id,
                guild_id=ctx.guild.id
            )
        if not reaction_role:
            raise Exception(f'There is no Reaction Role configured on this server with the ID \'{reaction_role_id}\'.')

        definition_lines = await _converters.ReactionRoleConverter(reaction_role).to_text(ctx.guild, True)
        await _utils.discord.reply_lines(ctx, definition_lines)

        delete, _, _ = await _utils.discord.inquire_for_true_false(ctx, f'Do you really want to delete the Reaction Role {reaction_role} as defined above?')
        if delete:
            delete, _, _ = await _utils.discord.inquire_for_true_false(ctx, f'Do you REALLY, REALLY want to delete the Reaction Role {reaction_role} as defined above?')
            if delete:
                if reaction_role.is_active:
                    cmd = self.bot.get_command('reactionrole deactivate')
                    await ctx.invoke(cmd, reaction_role_id=reaction_role_id)
                with _model.orm.create_session() as session:
                    reaction_role = _model.orm.get_by_id(_model.ReactionRole, session, reaction_role_id)
                    reaction_role.delete(session)
                await _utils.discord.reply(ctx, f'Success. The Reaction Role {reaction_role} has been deleted.', mention_author=True)
        if not delete:
            await _utils.discord.reply(ctx, f'Aborted. The Reaction Role {reaction_role} has not been deleted.', mention_author=True)


    @_commands.guild_only()
    @_commands.bot_has_guild_permissions(manage_roles=True)
    @_commands.has_guild_permissions(manage_roles=True)
    @base.command(name='edit', brief='Edit a Reaction Role')
    async def edit(self, ctx: _commands.Context, reaction_role_id: int) -> None:
        """
        Edits an inactive Reaction Role with the given ID on this server. Starts an assistant guiding through the process.
        Reaction Role IDs can be retrieved via the command: vivi reactionrole list

        Usage:
          vivi reactionrole edit [reaction_role_id]

        Parameters:
          reaction_role_id: Mandatory. The ID of an inactive Reaction Role on this server.

        Examples:
          vivi reactionrole edit 1 - Attempts to edit the Reaction Role with the ID 1
        """
        _utils.assert_.authorized_channel_or_server_manager(ctx, _bot_settings.AUTHORIZED_CHANNEL_IDS)
        with _model.orm.create_session() as session:
            reaction_role = _model.orm.get_first_filtered_by(
                _model.ReactionRole,
                session,
                id=reaction_role_id,
                guild_id=ctx.guild.id
            )
        if not reaction_role:
            raise Exception(f'There is no Reaction Role configured on this server with the ID \'{reaction_role_id}\'.')

        abort_text = f'Aborted. The Reaction Role {reaction_role} has not been edited.'

        if reaction_role.is_active:
            deactivate, _, _ = await _utils.discord.inquire_for_true_false(ctx, f'The Reaction Role {reaction_role} is currently active and cannot be edited, do you want to deactivate it now?')
            if deactivate:
                cmd = self.bot.get_command('reactionrole deactivate')
                await ctx.invoke(cmd, reaction_role_id=reaction_role.id)
            else:
                await _utils.discord.reply(ctx, abort_text)
                return

        actions = {
            'Edit details': edit_details,
            'Edit Role Changes': {
                'Add new Role Change': add_role_change,
                'Edit Role Change': edit_role_change,
                'Delete Role Change': remove_role_change,
            },
            'Edit Requirements': {
                'Add new Requirement': add_role_requirement,
                'Delete Requirement': remove_role_requirement,
            },
        }

        keep_editing = True
        while keep_editing:
            current_actions = dict(actions)
            selected_action: _Callable = None
            while current_actions:
                selector = _utils.Selector(
                    ctx,
                    None,
                    list(current_actions.keys()),
                    title=f'Editing Reaction Role {reaction_role}\nPlease select an action:'
                )
                selected, selected_action = await selector.wait_for_option_selection()
                if not selected or selected_action is None:
                    await _utils.discord.reply(ctx, abort_text)
                    return

                action = current_actions[selected_action]

                if isinstance(action, dict):
                    current_actions = action
                else:
                    current_actions = None

            success, aborted = await action(reaction_role, ctx, abort_text)
            if not success and not aborted:
                await _utils.discord.reply(ctx, f'Failed to make changes to the Reaction Role {reaction_role}.')

            if aborted:
                keep_editing = False
                return
            else:
                keep_editing, _, _ = await _utils.discord.inquire_for_true_false(ctx, f'Do you want to make more changes to the Reaction Role {reaction_role}?')
            keep_editing = keep_editing or False
        with _model.orm.create_session() as session:
            reaction_role = _model.orm.merge(session, reaction_role)
            reaction_role.save(session)
        activate, _, _ = await _utils.discord.inquire_for_true_false(ctx, f'Finished editing Reaction Role {reaction_role}.\nDo you want to activate it now?')
        if activate:
            cmd = self.bot.get_command('reactionrole activate')
            await ctx.invoke(cmd, reaction_role_id=reaction_role.id)


    @_commands.guild_only()
    @base.group(name='list', brief='List reaction roles', invoke_without_command=True)
    async def list(self, ctx: _commands.Context, include_messages: bool = False) -> None:
        """
        Lists all Reaction Roles configured on this server.

        Usage:
          vivi reactionrole list <include_messages>

        Parameters:
          include_messages: Optional. Determines, if Reaction Role Change messages and embeds shall be printed. Defaults to False.

        Examples:
          vivi reactionrole list yes - Prints all Reaction Roles configured on this server including all messages and embeds to be sent on Role changes.
          vivi reactionrole list false - Prints all Reaction Roles configured on this server without any messages and embeds to be sent on Role changes.
        """
        _utils.assert_.authorized_channel_or_server_manager(ctx, _bot_settings.AUTHORIZED_CHANNEL_IDS)
        with _model.orm.create_session() as session:
            reaction_roles = _model.orm.get_all_filtered_by(
                _model.ReactionRole,
                session,
                guild_id=ctx.guild.id
            )
        if reaction_roles:
            lines = '\n\n'.join([(await _converters.ReactionRoleConverter(reaction_role).to_text(ctx.guild, include_messages)) for reaction_role in reaction_roles])
            await _utils.discord.reply_lines(ctx, lines)
        else:
            raise Exception('There are no Reaction Roles configured for this server.')


    @_commands.guild_only()
    @list.command(name='active', aliases=['enabled', 'on'], brief='List active reaction roles', invoke_without_command=True)
    async def list_active(self, ctx: _commands.Context, include_messages: bool = False) -> None:
        """
        Lists all active Reaction Roles configured on this server.

        Usage:
          vivi reactionrole list active <include_messages>

        Parameters:
          include_messages: Optional. Determines, if Reaction Role Change messages and embeds shall be printed. Defaults to False.

        Examples:
          vivi reactionrole list active yes - Prints all active Reaction Roles configured on this server including all messages and embeds to be sent on Role changes.
          vivi reactionrole list active false - Prints all active Reaction Roles configured on this server without any messages and embeds to be sent on Role changes.
        """
        _utils.assert_.authorized_channel_or_server_manager(ctx, _bot_settings.AUTHORIZED_CHANNEL_IDS)
        with _model.orm.create_session() as session:
            reaction_roles = _model.orm.get_all_filtered_by(
                _model.ReactionRole,
                session,
                guild_id=ctx.guild.id,
                is_active=True
            )
        if reaction_roles:
            outputs = [(await _converters.ReactionRoleConverter(reaction_role).to_text(ctx.guild, include_messages)) for reaction_role in reaction_roles]
            for output in outputs:
                for post in output:
                    await _utils.discord.reply(ctx, post)
        else:
            raise Exception('There are no active Reaction Roles configured for this server.')


    @_commands.guild_only()
    @list.command(name='inactive', aliases=['disabled', 'off'], brief='List inactive reaction roles', invoke_without_command=True)
    async def list_inactive(self, ctx: _commands.Context, include_messages: bool = False) -> None:
        """
        Lists all inactive Reaction Roles configured on this server.

        Usage:
          vivi reactionrole list inactive <include_messages>

        Parameters:
          include_messages: Optional. Determines, if Reaction Role Change messages and embeds shall be printed. Defaults to False.

        Examples:
          vivi reactionrole list inactive yes - Prints all inactive Reaction Roles configured on this server including all messages and embeds to be sent on Role changes.
          vivi reactionrole list inactive false - Prints all inactive Reaction Roles configured on this server without any messages and embeds to be sent on Role changes.
        """
        _utils.assert_.authorized_channel_or_server_manager(ctx, _bot_settings.AUTHORIZED_CHANNEL_IDS)
        with _model.orm.create_session() as session:
            reaction_roles = _model.orm.get_all_filtered_by(
                _model.ReactionRole,
                session,
                guild_id=ctx.guild.id,
                is_active=False
            )
        if reaction_roles:
            outputs = [(await _converters.ReactionRoleConverter(reaction_role).to_text(ctx.guild, include_messages)) for reaction_role in reaction_roles]
            for output in outputs:
                for post in output:
                    await _utils.discord.reply(ctx, post)
        else:
            raise Exception('There are no inactive Reaction Roles configured for this server.')





# ---------- Helper ----------

async def add_role_change(reaction_role: _model.ReactionRole, ctx: _commands.Context, abort_text: str) -> _Tuple[bool, bool]:
    """
    Returns: (success: bool, aborted: bool)
    """
    role_change_definition, aborted = await inquire_for_role_change_details(ctx, abort_text)
    if aborted:
        return False, aborted

    role_change = reaction_role.add_change(*role_change_definition)
    await _utils.discord.reply(ctx, f'```Added role change with ID \'{role_change.id}\' to Reaction Role {reaction_role}.```')
    return True, aborted


async def add_role_requirement(reaction_role: _model.ReactionRole, ctx: _commands.Context, abort_text: str) -> _Tuple[bool, bool]:
    """
    Returns: (success: bool, aborted: bool)
    """
    required_role_id, aborted = await inquire_for_role_requirement_add(ctx, abort_text)
    if aborted:
        return False, aborted

    role_requirement = await reaction_role.add_requirement(required_role_id)
    await _utils.discord.reply(ctx, f'```Added role requirement with ID \'{role_requirement.id}\' to Reaction Role {reaction_role}.```')
    return True, aborted


async def edit_details(reaction_role: _model.ReactionRole, ctx: _commands.Context, abort_text: str) -> _Tuple[bool, bool]:
    """
    Returns: (success: bool, aborted: bool)
    """
    details, aborted = await inquire_for_reaction_role_details(ctx, abort_text, reaction_role)
    if aborted:
        return False, aborted

    if details:
        name, emoji, channel_id, message_id = details
        reaction_role.update(
            name=name,
            channel_id=channel_id,
            message_id=message_id,
            reaction=emoji,
        )
        await _utils.discord.reply(ctx, f'```Updated details of Reaction Role {reaction_role}.```')
        return True, False
    return False, aborted


async def add_role_change(reaction_role: _model.ReactionRole, ctx: _commands.Context, abort_text: str) -> _Tuple[bool, bool]:
    """
    Returns: (success: bool, aborted: bool)
    """
    role_change_definition, aborted = await inquire_for_role_change_details(ctx, abort_text)
    if aborted:
        return False, aborted

    role_change = reaction_role.add_change(*role_change_definition)
    await _utils.discord.reply(ctx, f'```Added role change with ID \'{role_change.id}\' to Reaction Role {reaction_role}.```')
    return True, aborted


async def edit_role_change(reaction_role: _model.ReactionRole, ctx: _commands.Context, abort_text: str) -> _Tuple[bool, bool]:
    """
    Returns: (success: bool, aborted: bool)
    """
    role_change_count = len(reaction_role.role_changes)
    if not role_change_count:
        return True, False

    reaction_role_change: _model.ReactionRoleChange = None
    if role_change_count == 1:
        reaction_role_change = reaction_role.role_changes[0]
    else:
        options = {}
        for reaction_role_change in sorted(reaction_role.role_changes, key=lambda x: x.id):
            options[reaction_role_change.id] = _converters.ReactionRoleChangeConverter.to_text(ctx, reaction_role_change)
        selector = _utils.Selector(
            ctx,
            None,
            options,
            title=f'Please select a Reaction Role Change to be edited:'
        )
        selected, selected_id = await selector.wait_for_option_selection()
        if not selected or selected_id is None:
            return True, True
        reaction_role_change = [role_change for role_change in reaction_role.role_changes if role_change.id == selected_id][0]

    role_change_definition, aborted = await inquire_for_role_change_details(ctx, abort_text, reaction_role_change)
    if aborted:
        return False, aborted
    reaction_role_change.update(*role_change_definition)

    await _utils.discord.reply(ctx, f'```Edited Reaction Role Change with ID \'{reaction_role_change.id}\'.```')
    return True, aborted


async def inquire_for_reaction_role_details(ctx: _commands.Context, abort_text: str, reaction_role: _Optional[_model.ReactionRole] = None, name: str = None, emoji: str = None, message_link: str = None) -> _Tuple[_Optional[_Tuple[str, str, int, int]], bool]:
    """
    Inquires the Discord user for a message ID, a channel mention or ID, an emoji and a name.

    Returns:
    ```Tuple[
        details: Optional[
            Tuple[
                name: str,
                emoji: str,
                channel_id: int,
                message_id: int
            ],
            aborted: bool
        ]
    ]```
    """
    new_str = 'new ' if reaction_role else ''
    skip_text = 'Skipped.' if reaction_role else None
    aborted = False

    if reaction_role:
        await _utils.discord.send(ctx, f'> Current name is \'{reaction_role.name}\'.')
    prompt_lines = [f'What should be the {new_str}name for the reaction role?']
    while not name:
        name, aborted, skipped = await _utils.discord.inquire_for_text(ctx, '\n'.join(prompt_lines), abort_text=abort_text, skip_text=skip_text)
        if aborted:
            return None, aborted
        if skipped:
            name = None
            break

    if reaction_role:
        await _utils.discord.send(ctx, f'> Current emoji is \'{reaction_role.reaction}\'.')
    prompt_base_lines = [f'Specify the {new_str}emoji to be used as the reaction.']
    prompt_lines = []
    emoji = _utils.discord.get_emoji(ctx, emoji)
    while not emoji:
        prompt_lines.extend(prompt_base_lines)
        emoji, aborted, skipped = await _utils.discord.inquire_for_emoji(ctx, '\n'.join(prompt_lines), abort_text=abort_text, skip_text=skip_text)
        prompt_lines = []
        if aborted:
            return None, aborted
        if skipped:
            emoji = None
            break

        if not emoji:
            prompt_lines = ['This is not a valid emoji or I cannot use this emoji.']

    channel_id = None
    message_id = None
    if message_link:
        channel, message = await _utils.discord.get_channel_and_message_from_message_link(ctx, message_link)
        if channel:
            channel_id = channel.id
        if message:
            message_id = message.id

    if reaction_role:
        await _utils.discord.send(ctx, f'> Current channel is <#{reaction_role.channel_id}>.\n> Current message is {_utils.discord.create_discord_link(ctx.guild.id, reaction_role.channel_id, reaction_role.message_id)}')
    prompt_base_lines = [f'Specify the full link to the {new_str}message, which the reaction shall be added to.']
    prompt_lines = []
    while not channel_id and not message_id:
        prompt_lines.extend(prompt_base_lines)
        message_link, aborted, skipped = await _utils.discord.inquire_for_message_link(ctx, '\n'.join(prompt_lines), abort_text=abort_text, skip_text=skip_text)
        prompt_lines = []
        if aborted:
            return None, aborted
        if skipped:
            message_link = None
            channel_id = None
            message_id = None
            break

        if message_link:
            channel, message = await _utils.discord.get_channel_and_message_from_message_link(ctx, message_link)
            if not channel:
                prompt_lines = ['This link points to a channel that is not on this server or that I cannot access.']
            elif not message:
                prompt_lines = ['This link points to a message that does not exist or that I cannot access.']
            else:
                channel_id = channel.id
                message_id = message.id
        else:
            prompt_lines = ['This is not a valid message link.']

    return (name, emoji, channel_id, message_id), aborted


async def inquire_for_role_change_details(ctx: _commands.Context, abort_text: str, reaction_role_change: _model.ReactionRoleChange = None) -> _Tuple[_Optional[_Tuple[int, bool, bool, _Optional[str], _Optional[int], _Optional[str]]], bool]:
    """
    Returns:
    ```Tuple[
        role_reaction_change: Optional[
            Tuple[
                role_id: int,
                add: bool,
                allow_toggle: bool,
                message_text: _Optional[str],
                message_channel_id: _Optional[int],
                message_embed: _Optional[str]
            ]
        ],
        aborted: bool
    ]```
    """
    skip_text = 'Skipped.' if reaction_role_change else None
    role: _discord.Role = None
    add: bool = None
    allow_toggle: bool = None
    role_change_message_content: str = None
    role_change_message_channel_id: int = None
    role_change_message_embed: str = None

    add_remove_prompt_message = 'Do you want to add or to remove a role?'
    if reaction_role_change:
        add = reaction_role_change.add
        add_remove_prompt_message += f'\nCurrent value: {"add" if add else "remove"}'
    add, aborted, skipped = await _utils.discord.inquire_for_add_remove(ctx, add_remove_prompt_message, abort_text=abort_text, skip_text=skip_text)
    if aborted:
        return None, aborted
    if skipped:
        add = reaction_role_change.add

    add_text = 'add' if add else 'remove'
    not_add_text = 'remove' if add else 'add'

    prompt_text_lines_base = [
        f'Which role do you want to {add_text}?'
    ]
    if reaction_role_change:
        current_role: _discord.Role = ctx.guild.get_role(reaction_role_change.role_id)
        prompt_text_lines_base.append(f'Current role: {current_role.name if current_role else f"the currently configured role (ID: {reaction_role_change.role_id}) does not exist"}')
    prompt_text_lines = []
    while role is None:
        prompt_text_lines.extend(prompt_text_lines_base)
        role, aborted, skipped = await _utils.discord.inquire_for_role(ctx, '\n'.join(prompt_text_lines), abort_text=abort_text, skip_text=skip_text)
        if aborted:
            return None, aborted
        if skipped:
            role = current_role
            break

        prompt_text_lines = []
        if role:
            if role.is_bot_managed() or role.is_integration() or role.is_default() or role.is_premium_subscriber():
                prompt_text_lines.append(f'I cannot add or remove the role {role.name}. It is either managed by bot or integration, the everyone role or the Nitro Server Booster role.')
                role = None
            elif role.position >= ctx.guild.me.roles[-1].position:
                prompt_text_lines.append(f'I am not allowed to add or remove the role {role.name}. It is higher than my highest role.')
                role = None
        else:
            prompt_text_lines.append('This is not a valid role mention or ID.')

    allow_toggle_prompt_message = f'Do you want to the role to be toggleable? Removing one\'s reaction would then {not_add_text} the role again.'
    if reaction_role_change:
        allow_toggle_prompt_message += f'\nCurrent value: {reaction_role_change.allow_toggle}'
    allow_toggle, aborted, skipped = await _utils.discord.inquire_for_true_false(ctx, allow_toggle_prompt_message, abort_text=abort_text, skip_text=skip_text)
    if aborted:
        return None, aborted
    if skipped:
        allow_toggle = reaction_role_change.allow_toggle

    add_message_prompt_message = f'Do you want to add a message that should be posted to a text channel, when a user gets the role `{role.name}` {add_text}ed?'
    add_message_current_value = None
    if reaction_role_change:
        add_message_current_value = reaction_role_change.message_channel_id and (reaction_role_change.message_content or reaction_role_change.message_embed)
        add_message_prompt_message += f'\nCurrent value: {add_message_current_value}'
    add_message, aborted, skipped = await _utils.discord.inquire_for_true_false(ctx, add_message_prompt_message, abort_text=abort_text)
    if aborted:
        return None, aborted
    if skipped:
        add_message = False
        add_message_current_value = None
    if not add_message and add_message_current_value:
        remove_current_message, aborted, _ = await _utils.discord.inquire_for_true_false(ctx, f'Do you want to remove the current message that should be posted to a text channel, when a user gets the role `{role.name}` {add_text}ed?', abort_text=abort_text)
        if aborted:
            return None, aborted
        if not remove_current_message:
            role_change_message_channel_id = reaction_role_change.message_channel_id
            role_change_message_content = reaction_role_change.message_content
            role_change_message_embed = reaction_role_change.message_embed

    if add_message:
        prompt_text_lines_base = [
            f'Which text channel should receive the message to be posted, when a user gets the role `{role.name}` {add_text}ed?'
        ]
        if reaction_role_change:
            current_channel: _discord.TextChannel = await ctx.bot.fetch_channel(reaction_role_change.message_channel_id)
            prompt_text_lines_base.append(f'Current channel: {current_channel.mention if current_channel else f"the currently configured channel (ID: {reaction_role_change.message_channel_id}) is not accessible"}')
        prompt_text_lines = []

        while role_change_message_channel_id is None:
            prompt_text_lines.extend(prompt_text_lines_base)
            role_change_message_channel, aborted, skipped = await _utils.discord.inquire_for_text_channel(ctx, '\n'.join(prompt_text_lines), abort_text=abort_text, skip_text=skip_text)
            if aborted:
                return None, aborted
            if skipped:
                role_change_message_channel_id = reaction_role_change.message_channel_id
                break

            prompt_text_lines = []
            if role_change_message_channel:
                if not isinstance(role_change_message_channel, _discord.TextChannel):
                    prompt_text_lines.append('You need to select a text channel.')
                else:
                    role_change_message_channel_id = role_change_message_channel.id
            else:
                prompt_text_lines.append('This is not a valid channel mention or a channel ID.')

        content = None
        embed = None
        if reaction_role_change:
            content = reaction_role_change.message_content
            if reaction_role_change.message_embed:
                embed = await _utils.discord.get_embed_from_definition_or_url(reaction_role_change.message_embed)
        if content or embed:
            await _utils.discord.send(ctx, content, embed=embed)
        while role_change_message_content is None and role_change_message_embed is None:
            inquire_message_text = True
            if reaction_role_change and reaction_role_change.message_content:
                inquire_message_text, aborted, _ = await _utils.discord.inquire_for_true_false(ctx, 'Do you want to edit the above message content?', abort_text=abort_text)
                if aborted:
                    return None, aborted

            if not inquire_message_text:
                role_change_message_content = content

            while inquire_message_text and role_change_message_content is None:
                prompt_lines = [
                        f'Please type a message to be sent (max. {_utils.discord.settings.MESSAGE_MAXIMUM_CHARACTER_COUNT} characters). The following variables are available:',
                        _utils.discord.PLACEHOLDERS.replace('`', '')
                    ]
                role_change_message_content, aborted, skipped = await _utils.discord.inquire_for_text(ctx, '\n'.join(prompt_lines), abort_text=abort_text, skip_text='Skipped.')
                if aborted:
                    return None, aborted
                if skipped:
                    break

            inquire_message_embed = True
            if reaction_role_change and reaction_role_change.message_embed:
                inquire_message_embed, aborted, _ = await _utils.discord.inquire_for_true_false(ctx, 'Do you want to edit the above embed?', abort_text=abort_text)
                if aborted:
                    return None, aborted

            while inquire_message_embed and role_change_message_embed is None:
                prompt_lines = [
                        'Please type a definition of an embed to be sent. The following variables are available:',
                        _utils.discord.PLACEHOLDERS.replace('`', '')
                ]
                role_change_message_embed, aborted, skipped = await _utils.discord.inquire_for_embed_definition(ctx, '\n'.join(prompt_lines), abort_text=abort_text, skip_text='Skipped.')
                if aborted:
                    return None, aborted
                if skipped:
                    role_change_message_embed = None
                    embed = None
                    break

                if role_change_message_embed:
                    embed = _json.loads(role_change_message_embed, cls=_utils.discord.EmbedLeovoelDecoder)
                else:
                    embed = None

            if role_change_message_content or role_change_message_embed:
                await _utils.discord.send(ctx, role_change_message_content, embed=embed)
                accept_message, aborted, _ = await _utils.discord.inquire_for_true_false(ctx, 'Do you want to use this message?', abort_text=abort_text)
                if aborted:
                    return None, aborted

                if not accept_message:
                    role_change_message_content = None
                    role_change_message_embed = None

    return (
        role.id,
        add,
        allow_toggle,
        role_change_message_content,
        role_change_message_channel_id,
        role_change_message_embed,
    ), aborted


async def inquire_for_role_change_remove(ctx: _commands.Context, reaction_role_changes: _List[_model.ReactionRoleChange], abort_text: str) -> _Optional[_model.ReactionRoleChange]:
    current_role_changes = {change.id: change for change in reaction_role_changes}
    options = {change_id: _converters.ReactionRoleChangeConverter.to_text(ctx, current_role_changes[change_id]) for change_id in sorted(current_role_changes.keys())}
    selector = _utils.Selector[str](ctx, None, options)
    selected, selected_id = await selector.wait_for_option_selection()
    if not selected or selected_id is None:
        await _utils.discord.reply(ctx, abort_text)
        return None

    return current_role_changes[selected_id]


async def inquire_for_role_requirement_add(ctx: _commands.Context, abort_text: str) -> _Tuple[_Optional[int], bool]:
    """
    Returns: (role_id: Optional[int], aborted: bool)
    """
    role = None
    prompt_text_lines_base = [
        f'Which role do you want to require?',
    ]
    prompt_text_lines = []
    while role is None:
        prompt_text_lines.extend(prompt_text_lines_base)
        role, aborted, _ = await _utils.discord.inquire_for_role(ctx, '\n'.join(prompt_text_lines), abort_text=abort_text)
        if aborted:
            return None, aborted

        if not role:
            prompt_text_lines = ['This is not a valid role mention or ID.']
        elif role.is_bot_managed() or role.is_integration() or role.is_default() or role.is_premium_subscriber():
            prompt_text_lines = [f'I cannot add or remove the role {role.name}. It is either managed by bot or integration, the everyone role or the Nitro Server Booster role.']
    return role.id, aborted


async def inquire_for_role_requirement_remove(ctx: _commands.Context, reaction_role_requirements: _List[_model.ReactionRoleRequirement], abort_text: str) -> _model.ReactionRoleRequirement:
    current_role_requirements = {requirement.id: requirement for requirement in reaction_role_requirements}
    options = {requirement_id: _converters.ReactionRoleRequirementConverter.to_text(ctx, current_role_requirements[requirement_id]) for requirement_id in sorted(current_role_requirements.keys())}
    selector = _utils.Selector[str](ctx, None, options)
    selected, selected_id = await selector.wait_for_option_selection()
    if not selected or selected_id is None:
        await _utils.discord.reply(ctx, abort_text)
        return None

    return current_role_requirements[selected_id]


async def remove_role_change(reaction_role: _model.ReactionRole, ctx: _commands.Context, abort_text: str) -> _Tuple[bool, bool]:
    """
    Returns: (success: bool, aborted: bool)
    """
    role_change = await inquire_for_role_change_remove(ctx, reaction_role.role_changes, abort_text)
    if role_change:
        role: _discord.Role = ctx.guild.get_role(role_change.role_id)
        role_change_id = role_change.id
        await _utils.discord.reply(ctx, f'Removed role change (ID: {role_change_id}) for role \'{role.name}\' (ID: {role.id}).')
        return True, False
    return False, True


async def remove_role_requirement(reaction_role: _model.ReactionRole, ctx: _commands.Context, abort_text: str) -> _Tuple[bool, bool]:
    """
    Returns: (success: bool, aborted: bool)
    """
    role_requirement = await inquire_for_role_requirement_remove(ctx, reaction_role.role_requirements, abort_text)
    if role_requirement:
        role: _discord.Role = ctx.guild.get_role(role_requirement.role_id)
        role_requirement_id = role_requirement.id
        await _utils.discord.reply(ctx, f'Removed role requirement (ID: {role_requirement_id}) for role \'{role.name}\' (ID: {role.id}).')
        return True, False
    return False, True


def setup(bot: _model.PssApiDiscordBot):
    bot.add_cog(ReactionRoles(bot))
