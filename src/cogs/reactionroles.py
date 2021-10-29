import json as _json
from typing import Callable as _Callable
from typing import Dict as _Dict
from typing import List as _List
from typing import Optional as _Optional
from typing import Tuple as _Tuple

from discord import Message as _Message
from discord import RawReactionActionEvent as _RawReactionActionEvent
from discord import Role as _Role
from discord import TextChannel as _TextChannel
from discord.ext.commands import Bot as _Bot
from discord.ext.commands import Cog as _Cog
from discord.ext.commands import Context as _Context
from discord.ext.commands import group as _command_group
from discord.ext.commands import guild_only as _guild_only
from discord.ext.commands import has_guild_permissions as _has_guild_permissions
from discord.ext.commands.core import bot_has_guild_permissions as _bot_has_guild_permissions

from .. import utils as _utils
from ..converters import ReactionRoleConverter as _ReactionRoleConverter
from ..converters import ReactionRoleChangeConverter as _ReactionRoleChangeConverter
from ..converters import ReactionRoleRequirementConverter as _ReactionRoleRequirementConverter
from ..model import database as _database
from ..model.reaction_role import ReactionRole as _ReactionRole
from ..model.reaction_role import ReactionRoleChange as _ReactionRoleChange
from ..model.reaction_role import ReactionRoleRequirement as _ReactionRoleRequirement



class ReactionRoleCog(_Cog):
    """
    Commands for configuring Reaction Roles on this server.
    """
    def __init__(self, bot: _Bot):
        if not bot:
            raise ValueError('Parameter \'bot\' must not be None.')
        self.__bot: _Bot = bot
        self.__reaction_roles: _Dict[int, _ReactionRole] = []
        bot.loop.create_task(self.__initialize())


    @property
    def bot(self) -> _Bot:
        return self.__bot


    async def __initialize(self) -> None:
        self.__reaction_roles = await ReactionRoleCog._read_reaction_roles_from_db()


    @_Cog.listener()
    async def on_raw_reaction_add(self, payload: _RawReactionActionEvent) -> None:
        if payload.member.guild.me == payload.member:
            return

        reaction_roles: _List[_ReactionRole] = self.__reaction_roles.get(payload.guild_id, [])
        member_roles_ids = [role.id for role in payload.member.roles]
        for reaction_role in reaction_roles:
            is_active = reaction_role.is_active
            message_id_match = reaction_role.message_id == payload.message_id
            emoji_match = reaction_role.reaction == payload.emoji.name
            if is_active and message_id_match and emoji_match:
                member_meets_requirements = all(requirement.role_id in member_roles_ids for requirement in reaction_role.role_requirements)
                if member_meets_requirements:
                    await reaction_role.apply_add(payload.member)


    @_Cog.listener()
    async def on_raw_reaction_remove(self, payload: _RawReactionActionEvent) -> None:
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        member = guild.get_member(payload.user_id)
        if not member or member == guild.me:
            return

        reaction_roles: _List[_ReactionRole] = self.__reaction_roles.get(payload.guild_id, [])
        member_roles_ids = [role.id for role in member.roles]
        for reaction_role in reaction_roles:
            is_active = reaction_role.is_active
            message_id_match = reaction_role.message_id == payload.message_id
            emoji_match = reaction_role.reaction == payload.emoji.name
            if is_active and message_id_match and emoji_match:
                member_meets_requirements = all(requirement.role_id in member_roles_ids for requirement in reaction_role.role_requirements)
                if member_meets_requirements:
                    await reaction_role.apply_remove(member)


    @_guild_only()
    @_command_group(name='reactionrole', aliases=['rr'], brief='Set up reaction roles', invoke_without_command=True)
    async def base(self, ctx: _Context) -> None:
        await ctx.send_help('reactionrole')


    @_guild_only()
    @_bot_has_guild_permissions(manage_roles=True)
    @_has_guild_permissions(manage_roles=True)
    @base.group(name='activate', aliases=['enable', 'on'], brief='Activate a Reaction Role', invoke_without_command=True)
    async def activate(self, ctx: _Context, reaction_role_id: int) -> None:
        reaction_roles = [reaction_role for reaction_role in self.__reaction_roles[ctx.guild.id] if reaction_role.id == reaction_role_id]
        if reaction_roles:
            reaction_role = reaction_roles[0]
            if reaction_role.is_active:
                raise Exception(f'The Reaction Role {reaction_role} is already active.')
            if (await reaction_role.try_activate(ctx)):
                await ctx.reply(f'Activated Reaction Role {reaction_role}', mention_author=False)
            else:
                raise Exception(f'Failed to activate Reaction Role {reaction_role}.')
        else:
            raise Exception(f'There is no Reaction Role configured on this server having the ID `{reaction_role_id}`.')


    @_guild_only()
    @_bot_has_guild_permissions(manage_roles=True)
    @_has_guild_permissions(manage_roles=True)
    @activate.command(name='all', brief='Activate all Reaction Roles')
    async def activate_all(self, ctx: _Context) -> None:
        reaction_roles = list(self.__reaction_roles[ctx.guild.id])
        if reaction_roles:
            failed_reaction_roles: _List[_ReactionRole] = []
            for reaction_role in reaction_roles:
                if not (await reaction_role.try_activate(ctx)):
                    failed_reaction_roles.append(reaction_role)
            response_lines = [f'Activated {len(reaction_roles) - len(failed_reaction_roles)} of {len(reaction_roles)} Reaction Roles on this server.']
            if failed_reaction_roles:
                response_lines.append('Could not activate the following roles:')
                for failed_reaction_role in failed_reaction_roles:
                    response_lines.append(f'ID: {failed_reaction_role.id} - Name: {failed_reaction_role.name}')
            await ctx.reply('\n'.join(response_lines), mention_author=False)
        else:
            raise Exception(f'There are no Reaction Role configured on this server.')


    @_guild_only()
    @_bot_has_guild_permissions(manage_roles=True)
    @_has_guild_permissions(manage_roles=True)
    @base.command(name='add', brief='Add a reaction role')
    async def add(self, ctx: _Context) -> None:
        """
        Assistant for adding reaction roles

        [message_id] must be of a message in [channel]
        [name] may contain whitespace
        """
        abort_text = 'Aborted. No reaction role has been created.'

        await ctx.reply('\n'.join([
                '```Welcome to the Reaction Role assistent.',
                'A Reaction Role can be created in 3 steps:',
                '- The basic definition',
                '- Role Changes - Configure which roles should be added/removed',
                '- Role Requirements - Configure which roles will be required to activate the Reaction Role',
                '',
                'You\'ll be guided step by step.```',
                '_ _',
            ]), mention_author=True)

        name: str = None
        emoji: str = None
        channel_id: int = None
        message_id: int = None
        details, aborted = await inquire_for_reaction_role_details(ctx, abort_text)
        if aborted:
            return
        if details:
            name, emoji, channel_id, message_id = details

        # role, add, allow_toggle, channel, message
        role_reaction_changes: _List[_Tuple[_Role, bool, bool, _TextChannel, str]] = []
        # role
        role_reaction_requirements: _List[_Role] = []

        add_role_change = True
        while add_role_change:
            role_reaction_change, aborted = await inquire_for_role_change_add(ctx, abort_text)
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
            required_roles = ', '.join([ctx.guild.get_role(role_id).name for role_id in role_reaction_requirements])
            confirmation_prompt_lines.append(f'Required role(s) = {required_roles}')
        confirmation_prompt_lines.append(f'_Role Changes_')
        review_messages = []
        for i, (role_id, add, allow_toggle, message_text, message_channel_id, message_embed) in enumerate(role_reaction_changes, 1):
            role = ctx.guild.get_role(role_id)
            add_text = 'add' if add else 'remove'
            send_message_str = ''
            if message_channel_id:
                message_channel = ctx.guild.get_channel(message_channel_id)
                send_message_str = f' and send a message to {message_channel.mention} (review message text below)'
                review_messages.append((i, message_text))
            confirmation_prompt_lines.append(f'{i} = {add_text} role `{role.name}`{send_message_str}')
        prompts = [await ctx.reply('\n'.join(confirmation_prompt_lines), mention_author=False)]
        for role_change_number, msg in review_messages:
            prompts.append((await prompts[0].reply(f'__**Message for Role Change \#{role_change_number}**__\n{msg}', mention_author=False)))

        finish_setup = await _utils.discord.inquire_for_true_false(ctx, 'Do you want to set up the Reaction Role? (selecting \'no\' will abort the process.)')
        if not finish_setup:
            await ctx.reply(abort_text, mention_author=False)
            return

        reaction_role = await _ReactionRole.create(ctx.guild.id, channel_id, message_id, name, emoji)
        for role_reaction_change_def in role_reaction_changes:
            await reaction_role.add_change(*role_reaction_change_def)
        for role_id in role_reaction_requirements:
            await reaction_role.add_requirement(role_id)

        self.__reaction_roles.setdefault(ctx.guild.id, []).append(reaction_role)
        await ctx.reply(f'Successfully set up a Reaction Role {reaction_role}.\nDon\'t forget to activate it!', mention_author=False)


    @_guild_only()
    @_bot_has_guild_permissions(manage_roles=True)
    @_has_guild_permissions(manage_roles=True)
    @base.group(name='deactivate', aliases=['disable', 'off'], brief='Deactivate a Reaction Role', invoke_without_command=True)
    async def deactivate(self, ctx: _Context, reaction_role_id: int) -> None:
        reaction_roles = [reaction_role for reaction_role in self.__reaction_roles[ctx.guild.id] if reaction_role.id == reaction_role_id]
        if reaction_roles:
            reaction_role = reaction_roles[0]
            if not reaction_role.is_active:
                raise Exception(f'The Reaction Role {reaction_role} is already inactive.')
            if (await reaction_role.try_deactivate(ctx)):
                await ctx.reply(f'Deactivated Reaction Role {reaction_role}.', mention_author=False)
            else:
                raise Exception(f'Failed to deactivate Reaction Role {reaction_role}.')
        else:
            raise Exception(f'There is no Reaction Role configured on this server having the ID `{reaction_role_id}`.')


    @_guild_only()
    @_bot_has_guild_permissions(manage_roles=True)
    @_has_guild_permissions(manage_roles=True)
    @deactivate.command(name='all', brief='Deactivate all Reaction Roles')
    async def deactivate_all(self, ctx: _Context) -> None:
        reaction_roles = list(self.__reaction_roles[ctx.guild.id])
        if reaction_roles:
            for reaction_role in reaction_roles:
                await reaction_role.try_deactivate(ctx)
            await ctx.reply(f'Deactivated {len(reaction_roles)} Reaction Roles on this server.', mention_author=False)
        else:
            raise Exception(f'There are no Reaction Role configured on this server.')


    @_guild_only()
    @_bot_has_guild_permissions(manage_roles=True)
    @_has_guild_permissions(manage_roles=True)
    @base.group(name='delete', aliases=['remove'], brief='Delete a Reaction Role')
    async def delete(self, ctx: _Context, reaction_role_id: int) -> None:
        """
        Delete a Reaction Role
        """
        reaction_roles = [reaction_role for reaction_role in self.__reaction_roles[ctx.guild.id] if reaction_role.id == reaction_role_id]
        if not reaction_roles:
            raise Exception(f'There is no Reaction Role configured on this server with the ID \'{reaction_role_id}\'.')

        reaction_role: _ReactionRole = reaction_roles[0]
        reaction_role_text = await _ReactionRoleConverter(reaction_role).to_text(ctx.guild, True)
        await ctx.reply('\n'.join(reaction_role_text), mention_author=False)

        result = False
        delete = await _utils.discord.inquire_for_true_false(ctx, f'Do you really want to delete the Reaction Role {reaction_role} as defined above?')
        if delete:
            delete = await _utils.discord.inquire_for_true_false(ctx, f'Do you REALLY, REALLY want to delete the Reaction Role {reaction_role} as defined above?')
            if delete:
                result = await reaction_role.delete()
        if not delete:
            await ctx.reply(f'Aborted. The Reaction Role {reaction_role} has not been deleted.', mention_author=True)
            return
        if result:
            self.__reaction_roles[ctx.guild.id] = [reaction_role for reaction_role in self.__reaction_roles[ctx.guild.id] if not reaction_role.deleted]
            await ctx.reply(f'Success. The Reaction Role {reaction_role} has been deleted.', mention_author=True)
        else:
            await ctx.reply(f'Failed. The Reaction Role {reaction_role} has not been deleted.', mention_author=True)


    @_guild_only()
    @_bot_has_guild_permissions(manage_roles=True)
    @_has_guild_permissions(manage_roles=True)
    @base.command(name='edit', brief='Edit a Reaction Role')
    async def edit(self, ctx: _Context, reaction_role_id: int) -> None:
        """
        Edit deactivated Reaction Roles.
        """
        reaction_roles = [reaction_role for reaction_role in self.__reaction_roles[ctx.guild.id] if reaction_role.id == reaction_role_id]
        if not reaction_roles:
            raise Exception(f'There is no Reaction Role configured on this server with the ID \'{reaction_role_id}\'.')

        reaction_role: _ReactionRole = reaction_roles[0]
        if reaction_role.is_active:
            raise Exception(f'Cannot edit the Reaction Role {reaction_role}, because it is active.')

        abort_text = f'Aborted. The Reaction Role {reaction_role} has not been edited.'
        actions = {
            'Edit details': edit_details,
            'Edit Role Changes': {
                'Add new Role Change': add_role_change,
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
                    await ctx.reply(abort_text, mention_author=False)
                    return

                action = current_actions[selected_action]

                if isinstance(action, dict):
                    current_actions = action
                else:
                    current_actions = None

            success, aborted = await action(reaction_role, ctx, abort_text)
            if not success and not aborted:
                await ctx.reply(f'Failed to make changes to the Reaction Role {reaction_role}.')

            if aborted:
                keep_editing = False
            else:
                keep_editing, _, _ = await _utils.discord.inquire_for_true_false(ctx, f'Do you want to make more changes to the Reaction Role \'{reaction_role.name}\'?')
            if not keep_editing:
                keep_editing = False
        await ctx.reply(f'```Finished editing Reaction Role {reaction_role}.```', mention_author=False)


    @_guild_only()
    @base.group(name='list', brief='List reaction roles', invoke_without_command=True)
    async def list(self, ctx: _Context, include_messages: bool = False) -> None:
        reaction_roles: _List[_ReactionRole] = list(self.__reaction_roles[ctx.guild.id])
        if reaction_roles:
            outputs = [(await _ReactionRoleConverter(reaction_role).to_text(ctx.guild, include_messages)) for reaction_role in reaction_roles if not reaction_role.deleted]
            for output in outputs:
                for post in output:
                    await ctx.reply(post, mention_author=False)
        else:
            raise Exception('There are no Reaction Roles configured for this server.')


    @_guild_only()
    @list.command(name='active', aliases=['enabled', 'on'], brief='List active reaction roles', invoke_without_command=True)
    async def list_active(self, ctx: _Context, include_messages: bool = False) -> None:
        reaction_roles = [reaction_role for reaction_role in self.__reaction_roles[ctx.guild.id] if reaction_role.is_active and not reaction_role.deleted]
        if reaction_roles:
            outputs = [(await _ReactionRoleConverter(reaction_role).to_text(ctx.guild, include_messages)) for reaction_role in reaction_roles]
            for output in outputs:
                for post in output:
                    await ctx.reply(post, mention_author=False)
        else:
            raise Exception('There are no active Reaction Roles configured for this server.')


    @_guild_only()
    @list.command(name='inactive', aliases=['disabled', 'off'], brief='List inactive reaction roles', invoke_without_command=True)
    async def list_inactive(self, ctx: _Context, include_messages: bool = False) -> None:
        reaction_roles = [reaction_role for reaction_role in self.__reaction_roles[ctx.guild.id] if not reaction_role.is_active and not reaction_role.deleted]
        if reaction_roles:
            outputs = [(await _ReactionRoleConverter(reaction_role).to_text(ctx.guild, include_messages)) for reaction_role in reaction_roles]
            for output in outputs:
                for post in output:
                    await ctx.reply(post, mention_author=False)
        else:
            raise Exception('There are no inactive Reaction Roles configured for this server.')


    @staticmethod
    async def _read_reaction_roles_from_db() -> _Dict[int, _ReactionRole]:
        reaction_roles: _List[_ReactionRole] = []
        changes: _Dict[int, _ReactionRoleChange] = {}
        requirements: _Dict[int, _ReactionRoleRequirement] = {}

        query = f'SELECT * FROM {_ReactionRole.TABLE_NAME}'
        rows = await _database.fetchall(query)
        reaction_roles = [_ReactionRole(row[0], *row[3:]) for row in rows]

        query = f'SELECT * FROM {_ReactionRoleChange.TABLE_NAME}'
        rows = await _database.fetchall(query)
        for row in rows:
            changes.setdefault(row[3], []).append(_ReactionRoleChange(row[0], *row[3:]))

        query = f'SELECT * FROM {_ReactionRoleRequirement.TABLE_NAME}'
        rows = await _database.fetchall(query)
        for row in rows:
            requirements.setdefault(row[3], []).append(_ReactionRoleRequirement(row[0], *row[3:]))

        reaction_roles.sort(key=lambda rr: rr.id)
        result = {}
        for reaction_role in reaction_roles:
            if reaction_role.id in changes:
                reaction_role.update_changes(changes[reaction_role.id])
            if reaction_role.id in requirements:
                reaction_role.update_requirements(requirements[reaction_role.id])
            result.setdefault(reaction_role.guild_id, []).append(reaction_role)

        return result





async def add_role_change(reaction_role: _ReactionRole, ctx: _Context, abort_text: str) -> _Tuple[bool, bool]:
    """
    Returns: (success: bool, aborted: bool)
    """
    role_change_definition, aborted = await inquire_for_role_change_add(ctx, abort_text)
    if aborted:
        return False, aborted

    role_change = await reaction_role.add_change(*role_change_definition)
    await ctx.reply(f'```Added role change with ID \'{role_change.id}\' to Reaction Role {reaction_role}.```', mention_author=False)
    return True, aborted


async def add_role_requirement(reaction_role: _ReactionRole, ctx: _Context, abort_text: str) -> _Tuple[bool, bool]:
    """
    Returns: (success: bool, aborted: bool)
    """
    required_role_id, aborted = await inquire_for_role_requirement_add(ctx, abort_text)
    if aborted:
        return False, aborted

    role_requirement = await reaction_role.add_requirement(required_role_id)
    await ctx.reply(f'```Added role requirement with ID \'{role_requirement.id}\' to Reaction Role {reaction_role}.```', mention_author=False)
    return True, aborted


async def edit_details(reaction_role: _ReactionRole, ctx: _Context, abort_text: str) -> _Tuple[bool, bool]:
    """
    Returns: (success: bool, aborted: bool)
    """
    details, aborted = await inquire_for_reaction_role_details(ctx, abort_text, reaction_role)
    if aborted:
        return False, aborted

    if details:
        name, emoji, channel_id, message_id = details
        if (await reaction_role.update(channel_id, message_id, name, emoji)):
            await ctx.reply(f'```Updated details of Reaction Role {reaction_role}.```')
            return True, False
    return False, aborted


async def inquire_for_reaction_role_details(ctx: _Context, abort_text: str, reaction_role: _Optional[_ReactionRole] = None) -> _Tuple[_Optional[_Tuple[str, str, int, int]], bool]:
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

    name: str = None
    if reaction_role:
        await ctx.send(f'> Current name is \'{reaction_role.name}\'.')
    prompt_lines = [f'What should be the {new_str}name for the reaction role?']
    while not name:
        name, aborted, skipped = await _utils.discord.inquire_for_text(ctx, '\n'.join(prompt_lines), abort_text=abort_text, skip_text=skip_text)
        if aborted:
            return None, aborted
        if skipped:
            name = None
            break

    emoji: str = None
    if reaction_role:
        await ctx.send(f'> Current emoji is \'{reaction_role.reaction}\'.')
    prompt_base_lines = [f'Specify the {new_str}emoji to be used as the reaction.']
    prompt_lines = []
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

    channel_id: int = None
    message_id: int = None
    if reaction_role:
        await ctx.send(f'> Current channel is <#{reaction_role.channel_id}>.\n> Current message is {_utils.discord.create_discord_link(ctx.guild.id, reaction_role.channel_id, reaction_role.message_id)}')
    prompt_base_lines = [f'Specify the full link to the {new_str} message, which the reaction shall be added to.']
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


async def inquire_for_role_change_add(ctx: _Context, abort_text: str) -> _Tuple[_Optional[_Tuple[int, bool, bool, _Optional[str], _Optional[int]]], bool]:
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
    role: _Role = None
    add: bool = None
    allow_toggle: bool = None
    role_change_message_text: str = None
    role_change_message_channel_id: int = None
    role_change_message_embed: str = None

    add, aborted, _ = await _utils.discord.inquire_for_add_remove(ctx, 'Do you want to add or to remove a role?', abort_text=abort_text)
    if aborted:
        return None, aborted

    add_text = 'add' if add else 'remove'
    not_add_text = 'remove' if add else 'add'

    prompt_text_lines_base = [
        f'Which role do you want to {add_text}?'
    ]
    prompt_text_lines = []
    while role is None:
        prompt_text_lines.extend(prompt_text_lines_base)
        role, aborted, _ = await _utils.discord.inquire_for_role(ctx, '\n'.join(prompt_text_lines), abort_text=abort_text)
        if aborted:
            return None, aborted

        prompt_text_lines = []
        if role:
            if role.position >= ctx.guild.me.roles[-1].position:
                prompt_text_lines.append(f'I am not allowed to add or remove the role {role.name}. It is higher than my highest role.')
                role = None
        else:
            prompt_text_lines.append('This is not a valid role mention or ID.')

    allow_toggle, aborted, _ = await _utils.discord.inquire_for_true_false(ctx, f'Do you want to the role to be toggable? Removing one\'s reaction would then {not_add_text} the role again.', abort_text=abort_text)
    if aborted:
        return None, aborted

    add_message, aborted, _ = await _utils.discord.inquire_for_true_false(ctx, f'Do you want to add a message that should be posted to a text channel, when a user gets the role `{role.name}` {add_text}ed?', abort_text=abort_text)
    if aborted:
        return None, aborted

    if add_message:
        prompt_text_lines_base = [
            f'Which text channel should receive the message to be posted, when a user gets the role `{role.name}` {add_text}ed?'
        ]
        prompt_text_lines = []

        while role_change_message_channel_id is None:
            prompt_text_lines.extend(prompt_text_lines_base)
            role_change_message_channel, aborted, _ = await _utils.discord.inquire_for_text_channel(ctx, '\n'.join(prompt_text_lines), abort_text=abort_text)
            if aborted:
                return None, aborted

            prompt_text_lines = []
            if role_change_message_channel:
                if not isinstance(role_change_message_channel, _TextChannel):
                    prompt_text_lines.append('You need to select a text channel.')
                else:
                    role_change_message_channel_id = role_change_message_channel.id
            else:
                prompt_text_lines.append('This is not a valid channel mention or a channel ID.')

        while role_change_message_text is None and role_change_message_embed is None:
            prompt_text = '\n'.join((
                    'Please type a message to be sent. The following variables are available:',
                    _utils.discord.PLACEHOLDERS.replace('`', '')
                ))
            role_change_message_text, aborted, _ = await _utils.discord.inquire_for_text(ctx, prompt_text, abort_text=abort_text, skip_text='Skipped.')
            if aborted:
                return None, aborted

            prompt_text = '\n'.join((
                    'Please type a definition of an embed to be sent. The following variables are available:',
                    _utils.discord.PLACEHOLDERS.replace('`', '')
                ))
            role_change_message_embed, aborted, _ = await _utils.discord.inquire_for_embed_definition(ctx, prompt_text, abort_text=abort_text, skip_text='Skipped.')
            if aborted:
                return None, aborted
            if role_change_message_embed:
                embed = _json.loads(role_change_message_embed, cls=_utils.discord.EmbedLeovoelDecoder)
            else:
                embed = None

            if role_change_message_text or role_change_message_embed:
                await ctx.send(role_change_message_text, embed=embed)
                accept_message, aborted, _ = await _utils.discord.inquire_for_true_false(ctx, 'Do you want to use this message?', abort_text=abort_text)
                if aborted:
                    return None, aborted

                if not accept_message:
                    role_change_message_text = None
                    role_change_message_embed = None

    return (
        role.id,
        add,
        allow_toggle,
        role_change_message_text,
        role_change_message_channel_id,
        role_change_message_embed,
    ), aborted


async def inquire_for_role_change_remove(ctx: _Context, reaction_role_changes: _List[_ReactionRoleChange], abort_text: str) -> _Optional[_ReactionRoleChange]:
    current_role_changes = {change.id: change for change in reaction_role_changes}
    options = {change_id: _ReactionRoleChangeConverter.to_text(ctx, change) for change_id, change in current_role_changes.items()}
    selector = _utils.Selector[str](ctx, None, options)
    selected, selected_id = await selector.wait_for_option_selection()
    if not selected or selected_id is None:
        await ctx.reply(abort_text, mention_author=False)
        return None

    return current_role_changes[selected_id]


async def inquire_for_role_requirement_add(ctx: _Context, abort_text: str) -> _Tuple[_Optional[int], bool]:
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

        prompt_text_lines = ['This is not a valid role mention or ID.']
    return role.id, aborted


async def inquire_for_role_requirement_remove(ctx: _Context, reaction_role_requirements: _List[_ReactionRoleRequirement], abort_text: str) -> int:
    current_role_requirements = {requirement.id: requirement for requirement in reaction_role_requirements}
    options = {requirement_id: _ReactionRoleRequirementConverter.to_text(ctx, requirement) for requirement_id, requirement in current_role_requirements.items()}
    selector = _utils.Selector[str](ctx, None, options)
    selected, selected_id = await selector.wait_for_option_selection()
    if not selected or selected_id is None:
        await ctx.reply(abort_text, mention_author=False)
        return None

    return current_role_requirements[selected_id]


async def remove_role_change(reaction_role: _ReactionRole, ctx: _Context, abort_text: str) -> _Tuple[bool, bool]:
    """
    Returns: (success: bool, aborted: bool)
    """
    role_change = await inquire_for_role_change_remove(ctx, reaction_role.role_changes, abort_text)
    if role_change:
        role_change_id = role_change.id
        role = ctx.guild.get_role(role_change.role_id)
        await reaction_role.remove_change(role_change_id)
        await ctx.reply(f'Removed role change (ID: {role_change_id}) for role \'{role.name}\' (ID: {role.id}).', mention_author=False)
        return True, False
    return False, True


async def remove_role_requirement(reaction_role: _ReactionRole, ctx: _Context, abort_text: str) -> _Tuple[bool, bool]:
    """
    Returns: (success: bool, aborted: bool)
    """
    role_requirement = await inquire_for_role_requirement_remove(ctx, reaction_role.role_requirements, abort_text)
    if role_requirement:
        role_requirement_id = role_requirement.id
        role = ctx.guild.get_role(role_requirement.role_id)
        await reaction_role.remove_requirement(role_requirement_id)
        await ctx.reply(f'Removed role requirement (ID: {role_requirement_id}) for role \'{role.name}\' (ID: {role.id}).', mention_author=False)
        return True, False
    return False, True


def setup(bot: _Bot):
    bot.add_cog(ReactionRoleCog(bot))