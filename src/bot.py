import asyncio
from typing import Dict

import discord
from discord.ext import commands
from discord.ext.commands import Context
from discord.ext.commands.core import bot_has_guild_permissions

import app_settings
from confirmator import Confirmator
import database
import init


# ---------- Setup ----------

BOT = commands.Bot(
    command_prefix=commands.when_mentioned_or('vivi '),
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
    await ctx.reply('https://discordapp.com/oauth2/authorize?scope=bot&permissions=139519798336&client_id=895959886834331658', mention_author=False)





# ---------- Reaction Roles ----------

@BOT.group(name='reactionrole', aliases=['rr'], brief='Set up reaction roles', invoke_without_command=True)
async def cmd_reactionrole(ctx: Context) -> None:
    ctx.send_help('reactionrole')


@cmd_reactionrole.command(name='add', brief='Add a reaction role')
async def cmd_reactionrole_add(ctx: Context, message_id: int, emoji: str) -> None:
    """
    Assistant for adding reaction roles
    """








# ---------- Helper ----------





# ---------- Module init ----------

async def __initialize() -> None:
    await init.init()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(__initialize())
    BOT.run(app_settings.DISCORD_BOT_TOKEN)