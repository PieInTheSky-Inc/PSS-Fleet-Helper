import discord
from discord.ext import commands

import app_settings



# ---------- Setup ----------

BOT = commands.Bot(
    command_prefix=commands.when_mentioned_or('vivi '),
    intents=discord.Intents.all(),
    activity=discord.activity.Activity(type=discord.ActivityType.playing, name='vivi help')
)





# ---------- Event handlers ----------

@BOT.event
async def on_command_error(ctx: commands.Context, err: Exception) -> None:
    if app_settings.THROW_COMMAND_ERRORS:
        raise err

    if isinstance(err, commands.errors.CommandInvokeError):
        err = err.original
    error_type = type(err).__name__

    await ctx.reply(error_type, mention_author=False)


@BOT.event
async def on_ready() -> None:
    print(f'Bot logged in as {BOT.user.name} ({BOT.user.id})')
    print(f'Bot version: {app_settings.VERSION}')





# ---------- Basic role management ----------

@BOT.group(name='role', brief='Role management', invoke_without_command=True)
async def cmd_role(ctx: commands.Context) -> None:
    pass


@cmd_role.command(name='add', brief='Add a role to specified members')
async def cmd_role_add(ctx: commands.Context, role: discord.Role, *, user_ids: str) -> None:
    """
    Add one role to multiple members.
    """
    user_ids = set(user_ids.split(' '))
    users_added = []
    for user_id in user_ids:
        member = await ctx.guild.fetch_member(int(user_id))
        await member.add_roles(role)
        users_added.append(f'{member.display_name} ({user_id})')

    await ctx.reply(f'Added role {role} to members:\n{"\n".join(users_added)}', mention_author=False)


@cmd_role.command(name='clear', brief='Remove a role from all members')
async def cmd_role_clear(ctx: commands.Context, role: discord.Role) -> None:
    """
    Remove a specific role from all members.
    """
    for member in list(role.members):
        await member.remove_roles(role)

    await ctx.reply(f'Removed role {role} from all members.', mention_author=False)


@cmd_role.command(name='remove', brief='Remove a role from specified members')
async def cmd_role_remove(ctx: commands.Context, role: discord.Role, *, user_ids: str) -> None:
    """
    Remove one role from multiple members.
    """
    user_ids = set(user_ids.split(' '))
    users_added = []
    for user_id in user_ids:
        member = await ctx.guild.fetch_member(int(user_id))
        await member.remove_roles(role)
        users_added.append(f'{member.display_name} ({user_id})')

    await ctx.reply(f'Removed role {role} from members:\n{"\n".join(users_added)}', mention_author=False)




# ---------- Bot management ----------

@BOT.command(name='about', brief='General info about the bot')
async def cmd_about(ctx: commands.Context) -> None:
    info = {
        'Server count': len(BOT.guilds),
        'Member count': sum([guild.member_count for guild in BOT.guilds]),
        'Version': app_settings.VERSION,
        'Github': '<https://github.com/PieInTheSky-Inc/ViViBot>',
    }
    await ctx.reply('\n'.join([f'{key}: {value}' for key, value in info.items()]), mention_author=False)


@BOT.command(name='invite', brief='Produce invite link')
async def cmd_invite(ctx: commands.Context) -> None:
    await ctx.reply('https://discordapp.com/oauth2/authorize?scope=bot&permissions=139519839296&client_id=895959886834331658', mention_author=False)





if __name__ == '__main__':
    BOT.run(app_settings.DISCORD_BOT_TOKEN)