from discord import TextChannel as _TextChannel
from discord.ext.commands import Bot as _Bot
from discord.ext.commands import Cog as _Cog
from discord.ext.commands import Context as _Context
from discord.ext.commands import is_owner as _is_owner
from discord.ext.commands import group as _command_group

from model import utils as _utils





class ChecksCog(_Cog):
    def __init__(self, bot: _Bot) -> None:
        self.__bot = bot


    @_is_owner()
    @_command_group(name='check', hidden=True, invoke_without_command=False)
    async def base(self, ctx: _Context) -> None:
        pass


    @_is_owner()
    @base.command(name='channel')
    async def channel(self, ctx: _Context, channel: str) -> None:
        result = _utils.discord.get_text_channel(ctx, channel)
        if result:
            await ctx.reply(result.mention, mention_author=False)
        else:
            await ctx.reply(f'This is not a valid channel or I cannot access it:\n{channel}', mention_author=False)


    @_is_owner()
    @base.command(name='emoji')
    async def emoji(self, ctx: _Context, emoji: str) -> None:
        result = _utils.discord.get_emoji(ctx, emoji)
        if result:
            await ctx.reply(result, mention_author=False)
        else:
            await ctx.reply(f'This is not a valid emoji or I cannot access it:\n{emoji}', mention_author=False)


    @_is_owner()
    @base.command(name='member')
    async def member(self, ctx: _Context, *, member: str) -> None:
        result = _utils.discord.get_member(ctx, member)
        if result:
            await ctx.reply(result.mention, mention_author=False)
        else:
            await ctx.reply(f'This is not a valid member of this guild:\n{member}', mention_author=False)


    @_is_owner()
    @base.command(name='message')
    async def message(self, ctx: _Context, channel: _TextChannel, message_id: str) -> None:
        result = await _utils.discord.fetch_message(channel, message_id)
        if result:
            await ctx.reply(f'{result.content}\nBy {result.author.mention}', mention_author=False)
        else:
            await ctx.reply(f'This is not a valid message id or I cannot access the channel:\n{channel.mention}\n{message_id}', mention_author=False)


    @_is_owner()
    @base.command(name='role')
    async def role(self, ctx: _Context, role: str) -> None:
        result = _utils.discord.get_role(ctx, role)
        if result:
            await ctx.reply(f'{result.mention}\n{result.position}', mention_author=False)
        else:
            await ctx.reply(f'This is not a valid role:\n{role}', mention_author=False)