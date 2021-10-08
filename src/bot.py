import discord
from discord.ext import commands

import app_settings





BOT = commands.Bot(
    command_prefix=commands.when_mentioned_or('vivi '),
    intents=discord.Intents.all(),
    activity=discord.activity.Activity(type=discord.ActivityType.playing, name='vivi help')
)





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
        await member.add_roles(role.id)
        users_added.append(f'{member.display_name} ({user_id})')

    await ctx.reply(f'Added role {role} to members: {", ".join(users_added)}', mention_author=False)


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
        await member.remove_roles(role.id)
        users_added.append(f'{member.display_name} ({user_id})')

    await ctx.reply(f'Removed role {role} from members: {", ".join(users_added)}', mention_author=False)




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
    await ctx.reply('https://discordapp.com/oauth2/authorize?scope=bot&permissions=139251403840&client_id=895959886834331658', mention_author=False)





if __name__ == '__main__':
    BOT.run(app_settings.DISCORD_BOT_TOKEN)