import asyncio
from typing import Callable as _Callable
from typing import List as _List
from typing import Optional as _Optional
from typing import Tuple as _Tuple

import discord
from discord.ext import commands
from discord.ext.commands import Context
from discord.ext.commands.core import bot_has_guild_permissions

import app_settings
from confirmator import Confirmator
import model
from vm_converter import ReactionRoleConverter as _ReactionRoleConverter


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
    await ctx.reply('https://discordapp.com/oauth2/authorize?scope=bot&permissions=139519798336&client_id=895959886834331658', mention_author=False)





# ---------- Reaction Roles ----------

@VIVI.bot.group(name='reactionrole', aliases=['rr'], brief='Set up reaction roles', invoke_without_command=True)
async def cmd_reactionrole(ctx: Context) -> None:
    ctx.send_help('reactionrole')


@cmd_reactionrole.command(name='add', brief='Add a reaction role')
async def cmd_reactionrole_add(ctx: Context, channel: discord.TextChannel, message_id: int, emoji: str, *, name: str) -> None:
    """
    Assistant for adding reaction roles
    """
    try:
        reaction_message = await channel.fetch_message(message_id)
    except discord.NotFound as e:
        raise Exception(f'Could not find a message with the id `{message_id}` in channel {channel.mention}') from e

    if reaction_message.guild != ctx.guild:
        raise Exception(f'You need to select a message from this server.')

    abort_message = 'Aborted. No reaction role has been created.'

    welcome_message: discord.Message = await ctx.reply('\n'.join([
            'Welcome to the Reaction Role assistent.',
            'A Reaction Role can be created in 3 steps:',
            '- The basic definition (you\'ve already done this by calling this command)',
            '- **Role Changes** (which roles should be added/removed)',
            '- **Role Requirements** (which roles are required to activate a Reaction Role)',
            '_ _',
            'You\'ll be guided step by step.',
            '_ _',
        ]))

    # role, add, allow_toggle, channel, message
    role_reaction_changes: _List[_Tuple[discord.Role, bool, bool, discord.TextChannel, str]] = []
    # role
    role_reaction_requirements: _List[discord.Role] = []
    add_role_change = True

    while add_role_change:
        add: bool = await _request_for_add_remove(ctx, '> Do you want to add or to remove a role?', abort_message=abort_message)
        if add is None:
            return

        add_text = 'add' if add else 'remove'
        not_add_text = 'remove' if add else 'add'

        role: discord.Role = None
        prompt_message_lines_base = [
            f'> Which role do you want to {add_text}?',
            '> (Type a role ID or mention; type `abort` to abort.)'
        ]
        prompt_message_lines = list(prompt_message_lines_base)
        while role is None:
            prompt = await ctx.reply('\n'.join(prompt_message_lines), mention_author=False)
            reply = await _wait_for_reply(ctx, None, abort_message=abort_message)
            if not reply:
                return

            await prompt.delete()
            prompt_message_lines = []
            content = reply.content.strip()

            if content.lower() == 'abort':
                await ctx.reply(abort_message, mention_author=False)
                return

            if len(reply.role_mentions) > 1:
                prompt_message_lines.append('Only one role mention allowed.')
            elif len(reply.role_mentions) == 1:
                role = reply.role_mentions[0]
            else:
                try:
                    role_id = int(content)
                    role = ctx.guild.get_role(role_id)
                except:
                    prompt_message_lines.append('Send a role mention or a role ID.')

            prompt_message_lines = prompt_message_lines.extend(prompt_message_lines_base)

        allow_toggle: bool = await _request_for_yes_no(ctx, f'> Do you want to the role to be toggable? Removing one\'s reaction would then {not_add_text} the role again.', abort_message=abort_message)
        if allow_toggle is None:
            return

        add_message = await _request_for_yes_no(ctx, f'> Do you want to add a message that should be posted to a text channel, when a user gets the role `{role.name}` {add_text}ed?', abort_message=abort_message)
        if add_message is None:
            return

        role_change_message_channel: discord.TextChannel = None
        role_change_message_text: str = None
        if add_message:
            prompt_message_lines_base = [
                f'> Which text channel should receive the message to be posted, when a user gets the role `{role.name}` {add_text}ed?',
                '> (Type a channel ID or mention; type `abort` to abort.)'
            ]
            prompt_message_lines = list(prompt_message_lines_base)
            while role_change_message_channel is None:
                prompt = await ctx.reply('\n'.join(prompt_message_lines), mention_author=False)
                reply = await _wait_for_reply(ctx, None, abort_message=abort_message)
                if not reply:
                    return

                await prompt.delete()
                prompt_message_lines = []
                content = reply.content.strip()

                if content.lower() == 'abort':
                    await ctx.reply(abort_message, mention_author=False)
                    return

                if len(reply.channel_mentions) > 1:
                    prompt_message_lines.append('Only one channel mention allowed.')
                elif len(reply.channel_mentions) == 1:
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
                        '> Please type a message to be sent. The following variables are available:',
                        '> `{user}`: mentions the user who reacted',
                    ]), mention_author=False)
                role_change_message = await _wait_for_reply(ctx, None, abort_message=abort_message)
                if role_change_message is None:
                    return

                role_change_message_text = role_change_message.content
                role_change_message = await ctx.send(role_change_message_text)
                accept_message = await _request_for_yes_no(ctx, 'Do you want to use this message?', abort_message=abort_message)
                await role_change_message.delete()
                if accept_message is None:
                    return

                if not accept_message:
                    role_change_message_text = None

        role_reaction_changes.append((
            role,
            add,
            allow_toggle,
            role_change_message_channel if add_message else None,
            role_change_message_text if add_message else None
        ))
        add_role_change = await _request_for_yes_no(ctx, '> Do you want to add another **Role Change**?')
        if add_role_change is None:
            return

    add_role_requirement = await _request_for_yes_no(ctx, '> Do you want to add a **Role Requirement** (a role required to trigger this Reaction Role)?')
    if add_role_requirement is None:
        return

    while add_role_requirement:
        role: discord.Role = None
        prompt_message_lines_base = [
            f'> Which role do you want to require?',
            '> (Type a role ID or mention; type `abort` to abort.)'
        ]
        prompt_message_lines = list(prompt_message_lines_base)
        while role is None:
            prompt = await ctx.reply('\n'.join(prompt_message_lines), mention_author=False)
            reply = await _wait_for_reply(ctx, None, abort_message=abort_message)
            if not reply:
                return

            await prompt.delete()
            prompt_message_lines = []
            content = reply.content.strip()

            if content.lower() == 'abort':
                await ctx.reply(abort_message, mention_author=False)
                return

            if len(reply.role_mentions) > 1:
                prompt_message_lines.append('Only one role mention allowed.')
            elif len(reply.role_mentions) == 1:
                role = reply.role_mentions[0]
            else:
                try:
                    role_id = int(content)
                    role = ctx.guild.get_role(role_id)
                except:
                    prompt_message_lines.append('Send a role mention or a role ID.')

            prompt_message_lines.extend(prompt_message_lines_base)

        role_reaction_requirements.append(role)
        add_role_requirement = await _request_for_yes_no(ctx, 'Do you want to add another **Role Requirement**?')
        if add_role_requirement is None:
            return

    confirmation_prompt_lines = ['> **Creating a new Reaction Role**',
        f'> Name = {name}',
        f'> Message ID = {reaction_message.id}',
        f'> Emoji = {emoji}',
    ]
    if role_reaction_requirements:
        required_roles = ', '.join([role.name for role in role_reaction_requirements])
        confirmation_prompt_lines.append(f'> Required role(s) = {required_roles}')
    confirmation_prompt_lines.append(f'> _Role Changes_')
    review_messages = []
    for i, (role, add, allow_toggle, message_channel, message_text) in enumerate(role_reaction_changes, 1):
        add_text = 'add' if add else 'remove'
        send_message_str = ''
        if message_channel:
            send_message_str = f' and send a message to {message_channel.mention} (review message text below)'
            review_messages.append((i, message_text))
        confirmation_prompt_lines.append(f'{i} = {add_text} role `{role.name}`{send_message_str}')
    prompts = [await ctx.reply('\n'.join(confirmation_prompt_lines), mention_author=False)]
    for role_change_number, msg in review_messages:
        prompts.append((await ctx.reply(f'> __**Message for Role Change \#{role_change_number}**__\n> {msg}', mention_author=False)))

    finish_setup = await _request_for_yes_no(ctx, '> Do you want to set up the Reaction Role? (selecting _no_ will abort the process)')
    if finish_setup is None:
        return

    reaction_role_definition = await model.ReactionRole.create(ctx.guild.id, reaction_message.id, name, emoji)
    for role, add, allow_toggle, message_channel, message_text in role_reaction_changes:
        await reaction_role_definition.add_change(
            role.id,
            add,
            allow_toggle,
            message_text if message_channel else None,
            message_channel.id if message_channel else None,
        )
    for role in role_reaction_requirements:
        await reaction_role_definition.add_requirement(role.id)

    VIVI.reaction_roles.setdefault(ctx.guild.id, []).append(reaction_role_definition)
    await welcome_message.delete()
    await ctx.reply('Successfully set up a Reaction Role.', mention_author=False)


@cmd_reactionrole.command(name='activate', brief='Activate a Reaction Role')
async def cmd_reactionrole_activate(ctx: Context, reaction_role_id: int) -> None:
    reaction_roles = [reaction_role for reaction_role in VIVI.reaction_roles[ctx.guild.id] if reaction_role.id == reaction_role_id]
    if reaction_roles:
        reaction_role = reaction_roles[0]
        if reaction_role.is_active:
            raise Exception(f'The Reaction Role `{reaction_role.name}` with ID `{reaction_role.id}` is already active.')
        if (await reaction_role.update(is_active=True)):
            await ctx.reply(f'Activated Reaction Role `{reaction_role.name}` with ID `{reaction_role.id}`', mention_author=False)
        else:
            raise Exception(f'Failed to activate Reaction Role `{reaction_role.name}` with ID `{reaction_role.id}`.')
    else:
        raise Exception(f'There is no Reaction Role configured on this server having the ID `{reaction_role_id}`.')


@cmd_reactionrole.command(name='deactivate', brief='Deactivate a Reaction Role')
async def cmd_reactionrole_deactivate(ctx: Context, reaction_role_id: int) -> None:
    reaction_roles = [reaction_role for reaction_role in VIVI.reaction_roles[ctx.guild.id] if reaction_role.id == reaction_role_id]
    if reaction_roles:
        reaction_role = reaction_roles[0]
        if not reaction_role.is_active:
            raise Exception(f'The Reaction Role `{reaction_role.name}` with ID `{reaction_role.id}` is already inactive.')
        if (await reaction_role.update(is_active=False)):
            await ctx.reply(f'Deactivated Reaction Role `{reaction_role.name}` with ID `{reaction_role.id}`.', mention_author=False)
        else:
            raise Exception(f'Failed to deactivate Reaction Role `{reaction_role.name}` with ID `{reaction_role.id}`.')
    else:
        raise Exception(f'There is no Reaction Role configured on this server having the ID `{reaction_role_id}`.')


@cmd_reactionrole.group(name='list', brief='List reaction roles', invoke_without_command=True)
async def cmd_reactionrole_list(ctx: Context, include_messages: bool) -> None:
    reaction_roles = list(VIVI.reaction_roles[ctx.guild.id])
    if reaction_roles:
        outputs = [(await _ReactionRoleConverter(reaction_role).to_text(ctx.guild, include_messages)) for reaction_role in reaction_roles]
        for output in outputs:
            for post in output:
                await ctx.reply(post, mention_author=False)
    else:
        raise Exception('There are no Reaction Roles configured for this server.')


@cmd_reactionrole_list.command(name='active', brief='List reaction roles', invoke_without_command=True)
async def cmd_reactionrole_list_active(ctx: Context, include_messages: str) -> None:
    reaction_roles = [reaction_role for reaction_role in VIVI.reaction_roles[ctx.guild.id] if reaction_role.is_active]
    if reaction_roles:
        outputs = [(await _ReactionRoleConverter(reaction_role).to_text(ctx.guild, include_messages)) for reaction_role in reaction_roles]
        for output in outputs:
            for post in output:
                await ctx.reply(post, mention_author=False)
    else:
        raise Exception('There are no active Reaction Roles configured for this server.')


@cmd_reactionrole_list.command(name='inactive', brief='List reaction roles', invoke_without_command=True)
async def cmd_reactionrole_list_inactive(ctx: Context, include_messages: str) -> None:
    reaction_roles = [reaction_role for reaction_role in VIVI.reaction_roles[ctx.guild.id] if not reaction_role.is_active]
    if reaction_roles:
        outputs = [(await _ReactionRoleConverter(reaction_role).to_text(ctx.guild, include_messages)) for reaction_role in reaction_roles]
        for output in outputs:
            for post in output:
                await ctx.reply(post, mention_author=False)
    else:
        raise Exception('There are no inactive Reaction Roles configured for this server.')





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
            prompt_message,
            f'(Type `{true_str}` or `{false_str}`; type `abort` to abort.)'
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
        return (await ctx.bot.wait_for('message', check=check, timeout=timeout))
    except asyncio.TimeoutError:
        if abort_message:
            await ctx.reply(abort_message)
        return None




# ---------- Module init ----------

async def __initialize() -> None:
    await model.setup_model()
    await VIVI.initialize()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(__initialize())
    VIVI.bot.run(app_settings.DISCORD_BOT_TOKEN)