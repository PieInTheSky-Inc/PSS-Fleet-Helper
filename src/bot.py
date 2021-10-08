import discord
from discord.ext import commands
from discord.ext.commands.core import cooldown

import app_settings





BOT = commands.Bot(
    command_prefix='vivi ',
    intents=discord.Intents.all()
)





# ---------- Basic role management ----------

@BOT.group(name='role', invoke_without_command=True)
async def cmd_role(ctx: commands.Context) -> None:
    pass


@cmd_role.command(name='add', brief='Add a role to the specified members')
async def cmd_role_add(ctx: commands.Context, role: discord.Role, *, user_ids: str) -> None:
    """
    Add one role to many members.
    """
    user_ids = set(user_ids.split(' '))
    users_added = []
    for user_id in user_ids:
        member = await ctx.guild.fetch_member(int(user_id))
        await member.add_roles(role.id)
        users_added.append(f'{member.display_name} ({user_id})')

    await ctx.send(f'Added role {role} to members: {", ".join(users_added)}')


@cmd_role.command(name='clear', brief='Remove a role from all members')
async def cmd_role_clear(ctx: commands.Context, role: discord.Role) -> None:
    """
    Remove a specific role from all members.
    """
    for member in list(role.members):
        member.remove_roles(role)

    await ctx.send(f'Removed role {role} from all members.')




# ---------- Bot management ----------

@BOT.command(name='about', brief='General info about the bot')
async def cmd_about(ctx: commands.Context) -> None:
    info = {
        'Server count': len(BOT.guilds),
        'Member count': sum([guild.member_count for guild in BOT.guilds]),
        'Version': app_settings.VERSION,
    }
    await ctx.send('\n'.join([f'{key} {value}' for key, value in info.items()]))


@BOT.command(name='invite', brief='Produce invite link')
async def cmd_invite(ctx: commands.Context) -> None:
    await ctx.send('https://discordapp.com/oauth2/authorize?scope=bot&permissions=139251403840&client_id=895959886834331658')





if __name__ == '__main__':
    BOT.run(app_settings.DISCORD_BOT_TOKEN)