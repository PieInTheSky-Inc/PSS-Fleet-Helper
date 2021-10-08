import discord
from discord.ext import commands

import app_settings





BOT = commands.Bot(
    command_prefix='vv ',
    intents=discord.Intents.all()
)





# ---------- Basic role management ----------

@BOT.group(name='role', invoke_without_command=True)
async def cmd_role(ctx: commands.Context) -> None:
    pass


@cmd_role.command(name='add', brief='Add a role to the specified members')
async def cmd_role_add(ctx: commands.Context, role: discord.Role, *, user_ids: str) -> None:
    pass


@cmd_role.command(name='clear', brief='Remove a role from all members')
async def cmd_role_clear(ctx: commands.Context, role: discord.Role) -> None:
    pass





# ---------- Bot management ----------

@BOT.command(name='invite', brief='Produce invite link')
async def cmd_invite(ctx: commands.Context) -> None:
    ctx.send('https://discordapp.com/oauth2/authorize?scope=bot&permissions=139251403840&client_id=895959886834331658')





if __name__ == '__main__':
    BOT.run(app_settings.DISCORD_BOT_TOKEN)