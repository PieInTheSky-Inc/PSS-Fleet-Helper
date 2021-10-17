import asyncio
import re as _re
from typing import Callable as _Callable
from typing import List as _List
from typing import Optional as _Optional
from typing import Tuple as _Tuple

import discord
from discord.ext import commands
from discord.ext.commands import Context
from discord.ext.commands.core import bot_has_guild_permissions, has_guild_permissions, is_owner
import emoji as _emoji

import app_settings
from confirmator import Confirmator
import model
from model import utils
from selector import Selector
from vm_converter import ReactionRoleChangeConverter as _ReactionRoleChangeConverter
from vm_converter import ReactionRoleConverter as _ReactionRoleConverter
from vm_converter import ReactionRoleRequirementConverter as _ReactionRoleRequirementConverter


# ---------- Setup ----------

VIVI = model.ViViBot(commands.Bot(
        command_prefix=commands.when_mentioned_or('vivi '),
        intents=discord.Intents.all(),
        activity=discord.activity.Activity(type=discord.ActivityType.playing, name='vivi help')
    ))





# ---------- Event handlers ----------

@VIVI.bot.event
async def on_command_error(ctx: Context, err: Exception) -> None:
    if app_settings.THROW_COMMAND_ERRORS:
        raise err

    if isinstance(err, commands.errors.CommandInvokeError):
        err = err.original
    error_type = type(err).__name__
    error_text = (err.args[0] or '') if err.args else ''
    msg = f'**{error_type}**'
    if error_text:
        msg += f'\n{error_text}'

    await ctx.reply(f'{msg}', mention_author=False)


@VIVI.bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent) -> None:
    if payload.member.guild.me == payload.member:
        return

    reaction_roles: _List[model.ReactionRole] = VIVI.reaction_roles.get(payload.guild_id, [])
    member_roles_ids = [role.id for role in payload.member.roles]
    for reaction_role in reaction_roles:
        is_active = reaction_role.is_active
        message_id_match = reaction_role.message_id == payload.message_id
        emoji_match = reaction_role.reaction == payload.emoji.name
        if is_active and message_id_match and emoji_match:
            member_meets_requirements = all(requirement.role_id in member_roles_ids for requirement in reaction_role.role_requirements)
            if member_meets_requirements:
                await reaction_role.apply_add(payload.member)


@VIVI.bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent) -> None:
    guild = VIVI.bot.get_guild(payload.guild_id)
    if not guild:
        return

    member = guild.get_member(payload.user_id)
    if not member or member == guild.me:
        return

    reaction_roles: _List[model.ReactionRole] = VIVI.reaction_roles.get(payload.guild_id, [])
    member_roles_ids = [role.id for role in member.roles]
    for reaction_role in reaction_roles:
        is_active = reaction_role.is_active
        message_id_match = reaction_role.message_id == payload.message_id
        emoji_match = reaction_role.reaction == payload.emoji.name
        if is_active and message_id_match and emoji_match:
            member_meets_requirements = all(requirement.role_id in member_roles_ids for requirement in reaction_role.role_requirements)
            if member_meets_requirements:
                await reaction_role.apply_remove(member)


@VIVI.bot.event
async def on_ready() -> None:
    print(f'Bot logged in as {VIVI.bot.user.name} ({VIVI.bot.user.id})')
    print(f'Bot version: {app_settings.VERSION}')





# ---------- Basic role management ----------

@VIVI.bot.group(name='role', brief='Role management', invoke_without_command=True)
async def cmd_role(ctx: Context) -> None:
    await ctx.send_help('role')


@bot_has_guild_permissions(manage_roles=True)
@commands.has_guild_permissions(manage_roles=True)
@cmd_role.command(name='add', brief='Add a role to specified members')
async def cmd_role_add(ctx: Context, role: discord.Role, *, user_ids: str) -> None:
    """
    Add one role to multiple members.
    """
    user_ids = set(user_ids.split(' '))
    confirmator = Confirmator(ctx, f'This command will add the role `{role}` to {len(user_ids)} members!')
    if (await confirmator.wait_for_option_selection()):
        users_added = []
        for user_id in user_ids:
            member = await ctx.guild.fetch_member(int(user_id))
            await member.add_roles(role)
            users_added.append(f'{member.display_name} ({user_id})')

        user_list = '\n'.join(sorted(users_added))

        await ctx.reply(f'Added role {role} to members:\n{user_list}', mention_author=False)


@bot_has_guild_permissions(manage_roles=True)
@commands.has_guild_permissions(manage_roles=True)
@cmd_role.command(name='clear', brief='Remove a role from all members')
async def cmd_role_clear(ctx: Context, role: discord.Role) -> None:
    """
    Remove a specific role from all members.
    """
    members = list(role.members)
    if len(members) > 0:
        confirmator = Confirmator(ctx, f'This command will remove the role `{role}` from {len(members)} members!')
        if (await confirmator.wait_for_option_selection()):
            users_removed = []
            for member in members:
                await member.remove_roles(role)
                users_removed.append(f'{member.display_name} ({member.id})')

            user_list = '\n'.join(sorted(users_removed))

            await ctx.reply(f'Removed role {role} from members:\n{user_list}', mention_author=False)
    else:
        await ctx.reply(f'There are no members with the role {role}.', mention_author=False)


@bot_has_guild_permissions(manage_roles=True)
@commands.has_guild_permissions(manage_roles=True)
@cmd_role.command(name='remove', brief='Remove a role from specified members')
async def cmd_role_remove(ctx: Context, role: discord.Role, *, user_ids: str) -> None:
    """
    Remove one role from multiple members.
    """
    user_ids = set(user_ids.split(' '))
    confirmator = Confirmator(ctx, f'This command removes the role `{role}` from {len(user_ids)} members.')
    if (await confirmator.wait_for_option_selection()):
        users_removed = []
        for user_id in user_ids:
            member = await ctx.guild.fetch_member(int(user_id))
            await member.remove_roles(role)
            users_removed.append(f'{member.display_name} ({user_id})')

        user_list = '\n'.join(sorted(users_removed))

        await ctx.reply(f'Removed role {role} from members:\n{user_list}', mention_author=False)





# ---------- Bot management ----------

@VIVI.bot.command(name='about', brief='General info about the bot')
async def cmd_about(ctx: Context) -> None:
    info = {
        'Server count': len(VIVI.bot.guilds),
        'Member count': sum([guild.member_count for guild in VIVI.bot.guilds]),
        'Version': app_settings.VERSION,
        'Github': '<https://github.com/PieInTheSky-Inc/ViViBot>',
    }
    await ctx.reply('\n'.join([f'{key}: {value}' for key, value in info.items()]), mention_author=False)


@VIVI.bot.command(name='invite', brief='Produce invite link')
async def cmd_invite(ctx: Context) -> None:
    await ctx.reply(f'https://discordapp.com/oauth2/authorize?scope=bot&permissions=139519798336&client_id={app_settings.DISCORD_BOT_CLIENT_ID}', mention_author=False)





# ---------- Reaction Roles ----------

@VIVI.bot.group(name='reactionrole', aliases=['rr'], brief='Set up reaction roles', invoke_without_command=True)
async def cmd_reactionrole(ctx: Context) -> None:
    await ctx.send_help('reactionrole')


@bot_has_guild_permissions(manage_roles=True)
@commands.has_guild_permissions(manage_roles=True)
@cmd_reactionrole.command(name='add', brief='Add a reaction role')
async def cmd_reactionrole_add(ctx: Context, channel: discord.TextChannel, message_id: int, emoji: str, *, name: str) -> None:
    """
    Assistant for adding reaction roles

    [message_id] must be of a message in [channel]
    [name] may contain whitespace
    """
    try:
        reaction_message = await channel.fetch_message(message_id)
    except discord.NotFound as e:
        raise Exception(f'Could not find a message with the id `{message_id}` in channel {channel.mention}') from e

    if reaction_message.guild != ctx.guild:
        raise Exception(f'You need to select a message from this server.')

    if _emoji.emoji_count(emoji) == 1:
        pass
    else:
        match = _re.match('<:\w+:(\d+)>', emoji)
        if not match:
            raise Exception(f'You need to select a valid emoji.')

    abort_message = 'Aborted. No reaction role has been created.'

    welcome_message: discord.Message = await ctx.reply('\n'.join([
            '```Welcome to the Reaction Role assistent.',
            'A Reaction Role can be created in 3 steps:',
            '- The basic definition (you\'ve already done this by calling this command)',
            '- **Role Changes** (which roles should be added/removed)',
            '- **Role Requirements** (which roles are required to activate a Reaction Role)',
            '',
            'You\'ll be guided step by step.```',
            '_ _',
        ]))

    # role, add, allow_toggle, channel, message
    role_reaction_changes: _List[_Tuple[discord.Role, bool, bool, discord.TextChannel, str]] = []
    # role
    role_reaction_requirements: _List[discord.Role] = []
    add_role_change = True

    while add_role_change:
        role_reaction_change = await _inquire_role_change_add(ctx, abort_message)
        if not role_reaction_change:
            return
        role_reaction_changes.append(role_reaction_change)

        add_role_change = await _request_for_yes_no(ctx, 'Do you want to add another >Role Change<?')
        if add_role_change is None:
            return

    add_role_requirement = await _request_for_yes_no(ctx, 'Do you want to add a >Role Requirement<\n(A role required to trigger this Reaction Role)?')
    if add_role_requirement is None:
        return

    while add_role_requirement:
        role_id = await _inquire_role_requirement_add(ctx, abort_message)
        if not role_id:
            return
        role_reaction_requirements.append(role_id)

        add_role_requirement = await _request_for_yes_no(ctx, 'Do you want to add another >Role Requirement<?')
        if add_role_requirement is None:
            return

    confirmation_prompt_lines = ['**Creating a new Reaction Role**',
        f'Name = {name}',
        f'Message ID = {reaction_message.id}',
        f'Emoji = {emoji}',
    ]
    if role_reaction_requirements:
        required_roles = ', '.join([ctx.guild.get_role(role_id).name for role_id in role_reaction_requirements])
        confirmation_prompt_lines.append(f'Required role(s) = {required_roles}')
    confirmation_prompt_lines.append(f'_Role Changes_')
    review_messages = []
    for i, (role_id, add, allow_toggle, message_text, message_channel_id) in enumerate(role_reaction_changes, 1):
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

    finish_setup = await _request_for_yes_no(ctx, 'Do you want to set up the Reaction Role? (selecting _no_ will abort the process)')
    if finish_setup is None:
        return

    reaction_role_definition = await model.ReactionRole.create(ctx.guild.id, channel.id, reaction_message.id, name, emoji)
    for role_reaction_change_def in role_reaction_changes:
        await reaction_role_definition.add_change(*role_reaction_change_def)
    for role_id in role_reaction_requirements:
        await reaction_role_definition.add_requirement(role_id)

    VIVI.reaction_roles.setdefault(ctx.guild.id, []).append(reaction_role_definition)
    await welcome_message.delete()
    await ctx.reply('Successfully set up a Reaction Role.', mention_author=False)


@bot_has_guild_permissions(manage_roles=True)
@commands.has_guild_permissions(manage_roles=True)
@cmd_reactionrole.group(name='activate', brief='Activate a Reaction Role', invoke_without_command=True)
async def cmd_reactionrole_activate(ctx: Context, reaction_role_id: int) -> None:
    reaction_roles = [reaction_role for reaction_role in VIVI.reaction_roles[ctx.guild.id] if reaction_role.id == reaction_role_id]
    if reaction_roles:
        reaction_role = reaction_roles[0]
        if reaction_role.is_active:
            raise Exception(f'The Reaction Role `{reaction_role.name}` with ID `{reaction_role.id}` is already active.')
        if (await reaction_role.try_activate(ctx)):
            await ctx.reply(f'Activated Reaction Role `{reaction_role.name}` with ID `{reaction_role.id}`', mention_author=False)
        else:
            raise Exception(f'Failed to activate Reaction Role `{reaction_role.name}` with ID `{reaction_role.id}`.')
    else:
        raise Exception(f'There is no Reaction Role configured on this server having the ID `{reaction_role_id}`.')


@bot_has_guild_permissions(manage_roles=True)
@commands.has_guild_permissions(manage_roles=True)
@cmd_reactionrole_activate.command(name='all', brief='Activate all Reaction Roles')
async def cmd_reactionrole_activate_all(ctx: Context) -> None:
    reaction_roles = list(VIVI.reaction_roles[ctx.guild.id])
    if reaction_roles:
        failed_reaction_roles: _List[model.ReactionRole] = []
        for reaction_role in reaction_roles:
            if not (await reaction_role.try_activate(ctx)):
                failed_reaction_roles.append(reaction_role)
        response_lines = [f'Activated {len(failed_reaction_roles) - len(reaction_roles)} of {len(reaction_roles)} Reaction Roles on this server.']
        if failed_reaction_roles:
            response_lines.append('Could not activate the following roles:')
            for failed_reaction_role in failed_reaction_roles:
                response_lines.append(f'ID: {failed_reaction_role.id} - Name: {failed_reaction_role.name}')
        await ctx.reply('\n'.join(response_lines), mention_author=False)
    else:
        raise Exception(f'There are no Reaction Role configured on this server.')


@bot_has_guild_permissions(manage_roles=True)
@commands.has_guild_permissions(manage_roles=True)
@cmd_reactionrole.group(name='deactivate', brief='Deactivate a Reaction Role', invoke_without_command=True)
async def cmd_reactionrole_deactivate(ctx: Context, reaction_role_id: int) -> None:
    reaction_roles = [reaction_role for reaction_role in VIVI.reaction_roles[ctx.guild.id] if reaction_role.id == reaction_role_id]
    if reaction_roles:
        reaction_role = reaction_roles[0]
        if not reaction_role.is_active:
            raise Exception(f'The Reaction Role `{reaction_role.name}` with ID `{reaction_role.id}` is already inactive.')
        if (await reaction_role.try_deactivate(ctx)):
            await ctx.reply(f'Deactivated Reaction Role `{reaction_role.name}` with ID `{reaction_role.id}`.', mention_author=False)
        else:
            raise Exception(f'Failed to deactivate Reaction Role `{reaction_role.name}` with ID `{reaction_role.id}`.')
    else:
        raise Exception(f'There is no Reaction Role configured on this server having the ID `{reaction_role_id}`.')


@bot_has_guild_permissions(manage_roles=True)
@commands.has_guild_permissions(manage_roles=True)
@cmd_reactionrole_deactivate.command(name='all', brief='Deactivate all Reaction Roles')
async def cmd_reactionrole_deactivate_all(ctx: Context) -> None:
    reaction_roles = list(VIVI.reaction_roles[ctx.guild.id])
    if reaction_roles:
        for reaction_role in reaction_roles:
            await reaction_role.try_deactivate(ctx)
        await ctx.reply(f'Deactivated {len(reaction_roles)} Reaction Roles on this server.', mention_author=False)
    else:
        raise Exception(f'There are no Reaction Role configured on this server.')


@bot_has_guild_permissions(manage_roles=True)
@commands.has_guild_permissions(manage_roles=True)
@cmd_reactionrole.group(name='delete', aliases=['remove'], brief='Delete a Reaction Role')
async def cmd_reactionrole_delete(ctx: Context, reaction_role_id: int) -> None:
    """
    Delete a Reaction Role
    """
    pass


@bot_has_guild_permissions(manage_roles=True)
@commands.has_guild_permissions(manage_roles=True)
@cmd_reactionrole.command(name='edit', brief='Edit a Reaction Role')
async def cmd_reactionrole_edit(ctx: Context, reaction_role_id: int) -> None:
    """
    Edit deactivated Reaction Roles.
    """
    reaction_roles = [reaction_role for reaction_role in VIVI.reaction_roles[ctx.guild.id] if reaction_role.id == reaction_role_id]
    keep_editing = True

    while reaction_roles and keep_editing:
        reaction_role = reaction_roles[0]
        if reaction_role.is_active:
            raise Exception(f'Cannot edit the active Reaction Role `{reaction_role.name}` with ID `{reaction_role.id}`.')

        abort_message = f'```Aborted. The Reaction Role \'{reaction_role.name}\' with ID \'{reaction_role.id}\' has not been edited.```'
        actions = {
            'Edit details': None,
            'Edit Role Changes': [
                'Add new Role Change',
                'Delete Role Change',
            ],
            'Edit Requirements': [
                'Add new Requirement',
                'Delete Requirement',
            ],
        }

        selector = Selector(
            ctx,
            None,
            actions,
            title=f'Editing Reaction Role {reaction_role.name} with ID `{reaction_role.id}`\nPlease select an action:'
        )
        selected, reply = await selector.wait_for_option_selection()
        if not selected or reply is None:
            await ctx.reply(abort_message, mention_author=False)

        await ctx.reply(f'```Selected \'{reply}\'.```', mention_author=False)
        if actions[reply]:
            selector = Selector[str](
                ctx,
                None,
                actions[reply],
                title=f'Editing Reaction Role {reaction_role.name} with ID `{reaction_role.id}`\nPlease select an action:'
            )
            selected, reply = await selector.wait_for_option_selection()
            if not selected or reply is None:
                await ctx.reply(abort_message, mention_author=False)

            await ctx.reply(f'```Selected \'{reply}\'.```', mention_author=False)
            reply = reply.lower()

            if 'add new' in reply:
                if 'change' in reply:
                    reaction_role_change = await _inquire_role_change_add(ctx, abort_message)
                    if not reaction_role_change:
                        return

                    await reaction_role.add_change(*reaction_role_change)
                    await ctx.reply(f'Added role change.', mention_author=False)
                elif 'requirement' in reply:
                    reaction_role_requirement = await _inquire_role_requirement_add(ctx, abort_message)
                    if not reaction_role_requirement:
                        return

                    await reaction_role.add_requirement(reaction_role_requirement)
                    await ctx.reply(f'Added role requirement.', mention_author=False)
            elif 'delete ' in reply:
                if 'change' in reply:
                    current_role_changes = list(reaction_role.role_changes)
                    options = [_ReactionRoleChangeConverter.to_text(ctx, change) for change in current_role_changes]
                    selector = Selector[str](
                        ctx,
                        None,
                        options,
                    )
                    selected, reply = await selector.wait_for_option_selection()
                    if not selected or reply is None:
                        await ctx.reply(abort_message, mention_author=False)

                    selected_index = options.index(reply)
                    role_change = current_role_changes[selected_index]
                    role = ctx.guild.get_role(role_change.role_id)
                    await reaction_role.remove_change(role_change.id)
                    await ctx.reply(f'Removed role change for role \'{role.name}\'.', mention_author=False)
                elif 'requirement' in reply:
                    current_role_requirements = list(reaction_role.role_requirements)
                    options = [_ReactionRoleRequirementConverter.to_text(ctx, change) for change in current_role_requirements]
                    selector = Selector[str](
                        ctx,
                        None,
                        options,
                    )
                    selected, reply = await selector.wait_for_option_selection()
                    if not selected or reply is None:
                        await ctx.reply(abort_message, mention_author=False)

                    selected_index = options.index(reply)
                    role_requirement = current_role_requirements[selected_index]
                    role = ctx.guild.get_role(role_requirement.role_id)
                    await reaction_role.remove_requirement(role_requirement.id)
                    await ctx.reply(f'Removed role requirement for role \'{role.name}\'.', mention_author=False)
        else:
            prompt = await ctx.reply(f'```Type a new name or \'skip\' to keep the current name ({reaction_role.name}).```', mention_author=False)
            reply = await _wait_for_reply(ctx, None, abort_message=abort_message)
            await prompt.delete()
            if reply is None:
                return

            content = reply.content.strip()
            new_name = content if content.lower() != 'skip' else None

            message_link = f'https://discord.com/channels/{ctx.guild.id}/{reaction_role.channel_id}/{reaction_role.message_id}'
            prompt = await ctx.reply(f'```Type a new message ID; Type \'skip\' to keep the current message id; Type \'abort\' to abort. Current message link:```{message_link}', mention_author=False)
            reply = await _wait_for_reply(ctx, None, abort_message=abort_message)
            await prompt.delete()
            if reply is None:
                return

            content = reply.content.strip()
            new_message_id = int(content) if content.lower() != 'skip' else None
            new_message = None
            new_channel_id = None
            while new_message_id and new_channel_id is None:
                prompt = await ctx.reply(f'```Type the channel ID or mention the channel of the new message; Type \'abort\' to abort.```', mention_author=False)
                reply = await _wait_for_reply(ctx, None, abort_message=abort_message)
                await prompt.delete()
                if reply is None:
                    return

                content = reply.content.strip()
                if len(reply.channel_mentions) > 0:
                    new_channel = reply.channel_mentions[0]
                    new_channel_id = new_channel.id
                else:
                    try:
                        new_channel_id = int(content)
                    except:
                        new_channel_id = None
                    if new_channel_id:
                        new_channel = ctx.guild.get_channel(new_channel_id)
                        if new_channel:
                            new_message = await new_channel.fetch_message(new_message_id)
                            if not new_message:
                                await reply.reply(f'```A message with ID `{new_message_id}` could not be found in {new_channel.mention}.```', mention_author=False)
                        else:
                            await reply.reply(f'```This is not a valid channel id or mention.```', mention_author=False)
                            new_channel_id = None

            new_emoji = None
            while new_emoji is None:
                prompt = await ctx.reply(f'```Type a new emoji; Type \'skip\' to keep the current emoji ({reaction_role.reaction}); Type \'abort\' to abort.```', mention_author=False)
                reply = await _wait_for_reply(ctx, None, abort_message=abort_message)
                await prompt.delete()
                if reply is None:
                    return

                content = reply.content.strip()
                if content.lower() == 'skip':
                    break

                new_emoji = utils.discord.get_emoji(ctx, content)
                if new_emoji is None:
                    await reply.reply(f'```This is not a valid emoji or I cannot use this emoji.```', mention_author=False)

            change_log_lines = [f'> Reaction Role with ID `{reaction_role.id}` has been updated.']
            if new_name:
                change_log_lines.append(f'> New name: `{new_name}`')
            if new_message_id:
                change_log_lines.append(f'> New message: ID `{new_message_id}` in channel {new_channel.mention} (https://discord.com/channels/{ctx.guild.id}/{new_channel_id}/{new_message_id})')
            if new_emoji:
                change_log_lines.append(f'> New emoji: {new_emoji}')

            if new_name or new_message_id or new_emoji:
                await reaction_role.update(channel_id=new_channel_id, message_id=new_message_id, name=new_name, reaction=new_emoji)
                await ctx.reply('\n'.join(change_log_lines))
            else:
                await ctx.reply('```No changes have been made.```', mention_author=False)
            keep_editing = await _request_for_yes_no(ctx, f'```Do you want to make more changes to the Reaction Role \'{reaction_role.name}\'?')
            if not keep_editing:
                keep_editing = False


@cmd_reactionrole.group(name='list', brief='List reaction roles', invoke_without_command=True)
async def cmd_reactionrole_list(ctx: Context, include_messages: bool = False) -> None:
    reaction_roles = list(VIVI.reaction_roles[ctx.guild.id])
    if reaction_roles:
        outputs = [(await _ReactionRoleConverter(reaction_role).to_text(ctx.guild, include_messages)) for reaction_role in reaction_roles]
        for output in outputs:
            for post in output:
                await ctx.reply(post, mention_author=False)
    else:
        raise Exception('There are no Reaction Roles configured for this server.')


@cmd_reactionrole_list.command(name='active', brief='List reaction roles', invoke_without_command=True)
async def cmd_reactionrole_list_active(ctx: Context, include_messages: bool = False) -> None:
    reaction_roles = [reaction_role for reaction_role in VIVI.reaction_roles[ctx.guild.id] if reaction_role.is_active]
    if reaction_roles:
        outputs = [(await _ReactionRoleConverter(reaction_role).to_text(ctx.guild, include_messages)) for reaction_role in reaction_roles]
        for output in outputs:
            for post in output:
                await ctx.reply(post, mention_author=False)
    else:
        raise Exception('There are no active Reaction Roles configured for this server.')


@cmd_reactionrole_list.command(name='inactive', brief='List reaction roles', invoke_without_command=True)
async def cmd_reactionrole_list_inactive(ctx: Context, include_messages: bool = False) -> None:
    reaction_roles = [reaction_role for reaction_role in VIVI.reaction_roles[ctx.guild.id] if not reaction_role.is_active]
    if reaction_roles:
        outputs = [(await _ReactionRoleConverter(reaction_role).to_text(ctx.guild, include_messages)) for reaction_role in reaction_roles]
        for output in outputs:
            for post in output:
                await ctx.reply(post, mention_author=False)
    else:
        raise Exception('There are no inactive Reaction Roles configured for this server.')





# ---------- Check commands ----------

@is_owner()
@VIVI.bot.group(name='check', hidden=True, invoke_without_command=False)
async def cmd_check(ctx: Context) -> None:
    pass


@is_owner()
@cmd_check.command(name='channel')
async def cmd_check_channel(ctx: Context, channel: str) -> None:
    result = utils.discord.get_text_channel(ctx, channel)
    if result:
        await ctx.reply(result.mention, mention_author=False)
    else:
        await ctx.reply(f'This is not a valid channel or I cannot access it:\n{channel}', mention_author=False)


@is_owner()
@cmd_check.command(name='emoji')
async def cmd_check_emoji(ctx: Context, emoji: str) -> None:
    result = utils.discord.get_emoji(ctx, emoji)
    if result:
        await ctx.reply(result, mention_author=False)
    else:
        await ctx.reply(f'This is not a valid emoji or I cannot access it:\n{emoji}', mention_author=False)


@is_owner()
@cmd_check.command(name='message')
async def cmd_check_message(ctx: Context, channel: discord.TextChannel, message_id: str) -> None:
    result = await utils.discord.get_message(channel, message_id)
    if result:
        await ctx.reply(f'{result.content}\nBy {result.author.mention}', mention_author=False)
    else:
        await ctx.reply(f'This is not a valid message id or I cannot access the channel:\n{channel.mention}\n{message_id}', mention_author=False)


@is_owner()
@cmd_check.command(name='role')
async def cmd_check_role(ctx: Context, role: str) -> None:
    result = utils.discord.get_role(ctx, role)
    if result:
        await ctx.reply(f'{result.mention}\n{result.position}', mention_author=False)
    else:
        await ctx.reply(f'This is not a valid role:\n{role}', mention_author=False)




# ---------- Helper ----------

def _check_for_add_remove(message: discord.Message) -> bool:
    return _check_for_boolean_string(message, 'add', 'remove')


def _check_for_yes_no(message: discord.Message) -> bool:
    return _check_for_boolean_string(message, 'yes', 'no')


def _check_for_boolean_string(message: discord.Message, true_str: str, false_str: str) -> bool:
    return message.content.lower() in (true_str, false_str, 'abort')


async def _request_for_add_remove(ctx: Context, prompt_message: str, timeout: float = 60.0, abort_message: str = None) -> _Optional[bool]:
    return await _request_for_boolean(ctx, prompt_message, 'add', 'remove', check=_check_for_add_remove, timeout=timeout, abort_message=abort_message)


async def _request_for_yes_no(ctx: Context, prompt_message: str, timeout: float = 60.0, abort_message: str = None) -> _Optional[bool]:
    return await _request_for_boolean(ctx, prompt_message, 'yes', 'no', check=_check_for_yes_no, timeout=timeout, abort_message=abort_message)


async def _request_for_boolean(ctx: Context, prompt_message: str, true_str: str, false_str: str, check: _Optional[_Callable[[discord.Message], bool]], timeout: float = 60.0, abort_message: str = None) -> _Optional[bool]:
    prompt = await ctx.reply('\n'.join([
            f'```{prompt_message}',
            f'(Type `{true_str}` or `{false_str}`; type `abort` to abort.)```'
        ]), mention_author=False)
    reply = await _wait_for_reply(ctx, check, timeout=timeout, abort_message=abort_message)
    await prompt.delete()
    if reply:
        result = reply.content.strip().lower()
        if result == 'abort':
            await ctx.reply(abort_message)
            return None
        return result == true_str
    return None


async def _wait_for_reply(ctx: Context, check: _Callable, timeout: float = 60.0, abort_message: str = None) -> _Optional[discord.Message]:
    try:
        result: discord.Message = await ctx.bot.wait_for('message', check=check, timeout=timeout)
        if result and abort_message and result.content.strip().lower() == 'abort':
            await ctx.reply(abort_message, mention_author=False)
            return None
        return result
    except asyncio.TimeoutError as e:
        if abort_message:
            await ctx.reply(abort_message, mention_author=False)
        return None


async def _inquire_role_change_add(ctx: Context, abort_message: str) -> _Optional[_Tuple[int, bool, bool, _Optional[str], _Optional[int]]]:
    add: bool = await _request_for_add_remove(ctx, 'Do you want to add or to remove a role?', abort_message=abort_message)
    if add is None:
        return

    add_text = 'add' if add else 'remove'
    not_add_text = 'remove' if add else 'add'

    role: discord.Role = None
    prompt_message_lines_base = [
        f'Which role do you want to {add_text}?',
        '(Type a role ID or mention; type `abort` to abort.)'
    ]
    prompt_message_lines = list(prompt_message_lines_base)
    while role is None:
        prompt_message_lines.insert(0, '```')
        prompt_message_lines.append('```')
        prompt = await ctx.reply('\n'.join(prompt_message_lines), mention_author=False)
        reply = await _wait_for_reply(ctx, None, abort_message=abort_message)
        if not reply:
            return None

        await prompt.delete()
        prompt_message_lines = []
        content = reply.content.strip()

        if content.lower() == 'abort':
            await ctx.reply(abort_message, mention_author=False)
            return None

        if len(reply.role_mentions) > 0:
            role = reply.role_mentions[0]
        else:
            try:
                role_id = int(content)
                role = ctx.guild.get_role(role_id)
            except:
                prompt_message_lines.append('Send a role mention or a role ID.')
        if role.position >= ctx.guild.me.roles[-1].position:
            prompt_message_lines.append(f'I am not allowed to add or remove the role {role.name}. It is higher than my highest role.')
            role_id = None
            role = None

        prompt_message_lines = prompt_message_lines.extend(prompt_message_lines_base)

    allow_toggle: bool = await _request_for_yes_no(ctx, f'Do you want to the role to be toggable? Removing one\'s reaction would then {not_add_text} the role again.', abort_message=abort_message)
    if allow_toggle is None:
        return None

    add_message = await _request_for_yes_no(ctx, f'Do you want to add a message that should be posted to a text channel, when a user gets the role `{role.name}` {add_text}ed?', abort_message=abort_message)
    if add_message is None:
        return None

    role_change_message_channel: discord.TextChannel = None
    role_change_message_text: str = None
    if add_message:
        prompt_message_lines_base = [
            f'Which text channel should receive the message to be posted, when a user gets the role `{role.name}` {add_text}ed?',
            '(Type a channel ID or mention; type `abort` to abort.)'
        ]
        prompt_message_lines = list(prompt_message_lines_base)
        while role_change_message_channel is None:
            prompt_message_lines.insert(0, '```')
            prompt_message_lines.append('```')
            prompt = await ctx.reply('\n'.join(prompt_message_lines), mention_author=False)
            reply = await _wait_for_reply(ctx, None, abort_message=abort_message)
            if not reply:
                return None

            await prompt.delete()
            prompt_message_lines = []
            content = reply.content.strip()

            if content.lower() == 'abort':
                await ctx.reply(abort_message, mention_author=False)
                return None

            if len(reply.channel_mentions) > 0:
                role_change_message_channel = reply.channel_mentions[0]
            else:
                try:
                    channel_id = int(content)
                    role_change_message_channel = ctx.guild.get_role(channel_id)
                except:
                    prompt_message_lines.append('Send a channel mention or a channel ID.')

            if not isinstance(role_change_message_channel, discord.TextChannel):
                prompt_message_lines.append('Select a text channel.')
                role_change_message_channel = None

            prompt_message_lines.extend(prompt_message_lines_base)

        while role_change_message_text is None:
            prompt = await ctx.reply('\n'.join([
                    '```Please type a message to be sent. The following variables are available:',
                    '{user}: mentions the user who reacted```',
                ]), mention_author=False)
            role_change_message = await _wait_for_reply(ctx, None, abort_message=abort_message)
            if not role_change_message:
                return

            role_change_message_text = role_change_message.content
            role_change_message = await ctx.send(role_change_message_text)
            accept_message = await _request_for_yes_no(ctx, 'Do you want to use this message?', abort_message=abort_message)
            await role_change_message.delete()
            if accept_message is None:
                return None

            if not accept_message:
                role_change_message_text = None

    return (
        role.id,
        add,
        allow_toggle,
        role_change_message_text if add_message else None,
        role_change_message_channel.id if add_message else None,
    )


async def _inquire_role_requirement_add(ctx: Context, abort_message: str) -> _Optional[int]:
    result = None
    prompt_message_lines_base = [
        f'Which role do you want to require?',
        '(Type a role ID or mention; type `abort` to abort.)'
    ]
    prompt_message_lines = list(prompt_message_lines_base)
    while result is None:
        prompt_message_lines.insert(0, '```')
        prompt_message_lines.append('```')
        prompt = await ctx.reply('\n'.join(prompt_message_lines), mention_author=False)
        reply = await _wait_for_reply(ctx, None, abort_message=abort_message)
        if not reply:
            return None

        await prompt.delete()
        prompt_message_lines = []
        content = reply.content.strip()

        if content.lower() == 'abort':
            await ctx.reply(abort_message, mention_author=False)
            return None

        if len(reply.role_mentions) > 1:
            prompt_message_lines.append('Only one role mention allowed.')
        elif len(reply.role_mentions) == 1:
            result = reply.role_mentions[0]
        else:
            try:
                role_id = int(content)
                result = ctx.guild.get_role(role_id)
            except:
                prompt_message_lines.append('Send a role mention or a role ID.')

        prompt_message_lines.extend(prompt_message_lines_base)
    return result.id





# ---------- Module init ----------

async def __initialize() -> None:
    await model.setup_model()
    await VIVI.initialize()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(__initialize())
    VIVI.bot.run(app_settings.DISCORD_BOT_TOKEN)