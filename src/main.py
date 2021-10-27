import asyncio
from typing import Callable as _Callable
from typing import List as _List
from typing import Optional as _Optional
from typing import Tuple as _Tuple

import discord
from discord.ext import commands
from discord.ext.commands import Context
from discord.ext.commands.core import bot_has_guild_permissions, is_owner

import app_settings
from confirmator import Confirmator
import model
from model import utils


# ---------- Setup ----------

BOT = commands.Bot(
    commands.when_mentioned_or('vivi '),
    intents=discord.Intents.all(),
    activity=discord.activity.Activity(type=discord.ActivityType.playing, name='vivi help')
)





# ---------- Event handlers ----------

@BOT.event
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


@BOT.event
async def on_ready() -> None:
    print(f'Bot logged in as {BOT.user.name} ({BOT.user.id})')
    print(f'Bot version: {app_settings.VERSION}')





# ---------- Basic role management ----------

@BOT.group(name='role', brief='Role management', invoke_without_command=True)
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

@BOT.command(name='about', brief='General info about the bot')
async def cmd_about(ctx: Context) -> None:
    info = {
        'Server count': len(BOT.guilds),
        'Member count': sum([guild.member_count for guild in BOT.guilds]),
        'Version': app_settings.VERSION,
        'Github': '<https://github.com/PieInTheSky-Inc/ViViBot>',
    }
    await ctx.reply('\n'.join([f'{key}: {value}' for key, value in info.items()]), mention_author=False)


@BOT.command(name='invite', brief='Produce invite link')
async def cmd_invite(ctx: Context) -> None:
    await ctx.reply(f'https://discordapp.com/oauth2/authorize?scope=bot&permissions=139519798336&client_id={app_settings.DISCORD_BOT_CLIENT_ID}', mention_author=False)





# ---------- Check commands ----------

@is_owner()
@BOT.group(name='check', hidden=True, invoke_without_command=False)
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
@cmd_check.command(name='member')
async def cmd_check_member(ctx: Context, *, member: str) -> None:
    result = utils.discord.get_member(ctx, member)
    if result:
        await ctx.reply(result.mention, mention_author=False)
    else:
        await ctx.reply(f'This is not a valid member of this guild:\n{member}', mention_author=False)


@is_owner()
@cmd_check.command(name='message')
async def cmd_check_message(ctx: Context, channel: discord.TextChannel, message_id: str) -> None:
    result = await utils.discord.fetch_message(channel, message_id)
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
    return discord.utils.check_for_boolean_string(message, ['add'], ['remove'])


def _check_for_yes_no(message: discord.Message) -> bool:
    return discord.utils.check_for_boolean_string(message, ['yes'], ['no'])


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


async def _inquire_role_change_add(ctx: Context, abort_text: str) -> _Optional[_Tuple[int, bool, bool, _Optional[str], _Optional[int]]]:
    add, aborted, _ = await utils.discord.inquire_for_add_remove(ctx, 'Do you want to add or to remove a role?', abort_text=abort_text)
    if aborted:
        return None

    add_text = 'add' if add else 'remove'
    not_add_text = 'remove' if add else 'add'

    role: discord.Role = None
    prompt_text_lines_base = [
        f'Which role do you want to {add_text}?'
    ]
    prompt_text_lines = []
    while role is None:
        prompt_text_lines.extend(prompt_text_lines_base)
        role, aborted, _ = await utils.discord.inquire_for_role(ctx, '\n'.join(prompt_text_lines), abort_text=abort_text)
        if aborted:
            return None

        prompt_text_lines = []
        if role:
            if role.position >= ctx.guild.me.roles[-1].position:
                prompt_text_lines.append(f'I am not allowed to add or remove the role {role.name}. It is higher than my highest role.')
                role = None
        else:
            prompt_text_lines.append('This is not a valid role mention or ID.')

    allow_toggle, aborted, _ = await utils.discord.inquire_for_true_false(ctx, f'Do you want to the role to be toggable? Removing one\'s reaction would then {not_add_text} the role again.', abort_text=abort_text)
    if aborted:
        return None

    add_message, aborted, _ = await utils.discord.inquire_for_true_false(ctx, f'Do you want to add a message that should be posted to a text channel, when a user gets the role `{role.name}` {add_text}ed?', abort_text=abort_text)
    if aborted:
        return None

    role_change_message_channel: discord.TextChannel = None
    role_change_message_text: str = None
    if add_message:
        prompt_text_lines_base = [
            f'Which text channel should receive the message to be posted, when a user gets the role `{role.name}` {add_text}ed?'
        ]
        prompt_text_lines = list(prompt_text_lines_base)
        while role_change_message_channel is None:
            prompt_text_lines.extend(prompt_text_lines_base)
            role_change_message_channel, aborted, _ = await utils.discord.inquire_for_text_channel(ctx, '\n'.join(prompt_text_lines), abort_text=abort_text)
            if aborted:
                return None

            prompt_text_lines = []
            if role_change_message_channel:
                if not isinstance(role_change_message_channel, discord.TextChannel):
                    prompt_text_lines.append('You need to select a text channel.')
                    role_change_message_channel = None
            else:
                prompt_text_lines.append('This is not a valid channel mention or a channel ID.')

        while role_change_message_text is None:
            prompt_text_lines = await ctx.reply('\n'.join([
                    'Please type a message to be sent. The following variables are available:',
                    '{user}: mentions the user who reacted```',
                ]), mention_author=False)
            prompt_text = utils.discord.get_prompt_text('\n'.join(prompt_text_lines), None, True, False)
            await ctx.reply('\n'.join(prompt_text))
            role_change_message = await utils.discord.wait_for_message(ctx, True)
            if not role_change_message:
                return None

            accept_message, aborted, _ = await utils.discord.inquire_for_message_confirmation(ctx, role_change_message, 'Do you want to use this message?', abort_text=abort_text)
            if aborted:
                return None

            if accept_message:
                role_change_message_text = role_change_message.content

    return (
        role.id,
        add,
        allow_toggle,
        role_change_message_text if add_message else None,
        role_change_message_channel.id if add_message else None,
    )


async def _inquire_role_requirement_add(ctx: Context, abort_text: str) -> _Optional[int]:
    role = None
    prompt_text_lines_base = [
        f'Which role do you want to require?',
    ]
    prompt_text_lines = []
    while role is None:
        prompt_text_lines.extend(prompt_text_lines_base)
        role, aborted, _ = await utils.discord.inquire_for_role(ctx, '\n'.join(prompt_text_lines), abort_text=abort_text)
        if aborted:
            return None

        prompt_text_lines = ['This is not a valid role mention or ID.']
    return role.id





# ---------- Module init ----------

async def __initialize() -> None:
    await model.setup_model()
    BOT.load_extension('reactionroles')


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(__initialize())
    BOT.run(app_settings.DISCORD_BOT_TOKEN)