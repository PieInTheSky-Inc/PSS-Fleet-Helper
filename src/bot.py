import discord
from discord.ext import commands

import app_settings


BOT = commands.Bot(command_prefix='vv ')


@BOT.group(name='role', invoke_without_command=True)
async def cmd_role(ctx: commands.Context) -> None:
    pass


@cmd_role.command(name='add')
async def cmd_role_add(ctx: commands.Context, role: discord.Role, *, user_ids: str) -> None:
    pass


@cmd_role.command(name='clear')
async def cmd_role_clear(ctx: commands.Context, role: discord.Role) -> None:
    pass


if __name__ == '__main__':
    BOT.run(app_settings.DISCORD_BOT_TOKEN)