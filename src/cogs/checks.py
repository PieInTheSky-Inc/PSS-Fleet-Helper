from discord import Role as _Role
from discord import TextChannel as _TextChannel
from discord.ext.commands import Bot as _Bot
from discord.ext.commands import Cog as _Cog
from discord.ext.commands import Context as _Context
from discord.ext.commands import is_owner as _is_owner
from discord.ext.commands import group as _command_group

from .. import utils as _utils



class ChecksCog(_Cog):
    def __init__(self, bot: _Bot) -> None:
        if not bot:
            raise ValueError('Parameter \'bot\' must not be None.')
        self.__bot = bot


    @property
    def bot(self) -> _Bot:
        return self.__bot


    @_is_owner()
    @_command_group(name='check', hidden=True, invoke_without_command=True)
    async def base(self, ctx: _Context) -> None:
        pass


    @_is_owner()
    @base.command(name='channel')
    async def channel(self, ctx: _Context, channel: str) -> None:
        result = _utils.discord.get_text_channel(ctx, channel)
        if result:
            await _utils.discord.reply(ctx, result.mention)
        else:
            lines = [
                f'This is not a valid channel or I cannot access it:',
                channel
            ]
            await _utils.discord.reply_lines(ctx, lines)


    @_is_owner()
    @base.command(name='emoji')
    async def emoji(self, ctx: _Context, emoji: str) -> None:
        result = _utils.discord.get_emoji(ctx, emoji)
        if result:
            await _utils.discord.reply(ctx, result)
        else:
            lines = [
                f'This is not a valid emoji or I cannot access it:',
                emoji
            ]
            await _utils.discord.reply_lines(ctx, lines)


    @_is_owner()
    @base.command(name='member')
    async def member(self, ctx: _Context, *, member: str) -> None:
        result = _utils.discord.get_member(ctx, member)
        if result:
            await _utils.discord.reply(ctx, result.mention)
        else:
            lines = [
                f'This is not a valid member of this server:',
                member
            ]
            await _utils.discord.reply_lines(ctx, lines)


    @_is_owner()
    @base.command(name='message')
    async def message(self, ctx: _Context, channel: _TextChannel, message_id: str) -> None:
        result = await _utils.discord.fetch_message(channel, message_id)
        if result:
            await _utils.discord.reply(ctx, f'{result.content}\nBy {result.author.mention}')
        else:
            lines = [
                f'This is not a valid message id or I cannot access the channel:',
                channel.mention,
                message_id
            ]
            await _utils.discord.reply_lines(ctx, lines)


    @_is_owner()
    @base.command(name='role')
    async def role(self, ctx: _Context, role: str) -> None:
        result: _Role = _utils.discord.get_role(ctx, role)
        if result:
            lines = [
                result.mention,
                str(result.position),
            ]
            await _utils.discord.reply_lines(ctx, lines)
        else:
            lines = [
                f'This is not a valid role:',
                role,
            ]
            await _utils.discord.reply_lines(ctx, lines)


def setup(bot: _Bot):
    bot.add_cog(ChecksCog(bot))