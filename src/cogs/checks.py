from discord import Role as _Role
from discord import TextChannel as _TextChannel
from discord.ext.commands import Bot as _Bot
from discord.ext.commands import Cog as _Cog
from discord.ext.commands import Context as _Context
from discord.ext.commands import is_owner as _is_owner
from discord.ext.commands import group as _command_group

from .. import bot_settings as _bot_settings
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
        """
        Provides commands for checking user input. Check out the subcommands.

        Usage:
          vivi check [subcommand]
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help('check')


    @_is_owner()
    @base.command(name='channel')
    async def channel(self, ctx: _Context, channel_id_or_mention: str) -> None:
        """
        Checks, if a channel with the provided ID or mention exists on this guild and can be accessed by the bot.

        Usage:
          vivi check channel [channel_id_or_mention]

        Parameters:
          channel_id_or_mention: Mandatory. A mention or an ID of a channel to be checked.

        Examples:
          vivi check channel 1
          vivi check channel #foobar
        """
        result = _utils.discord.get_text_channel(ctx, channel_id_or_mention)
        if result:
            await _utils.discord.reply(ctx, result.mention)
        else:
            lines = [
                f'This is not a valid channel or I cannot access it:',
                channel_id_or_mention
            ]
            await _utils.discord.reply_lines(ctx, lines)


    @_is_owner()
    @base.command(name='emoji')
    async def emoji(self, ctx: _Context, emoji: str) -> None:
        """
        Checks, if a given emoji exists on this guild or is a standard emoji and can be accessed by the bot.

        Usage:
          vivi check emoji [emoji]

        Parameters:
          emoji: Mandatory. A standard emoji or a custom emoji of the current guild.

        Examples:
          vivi check emoji 😁
          vivi check <:ayy:1>
        """
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
    async def member(self, ctx: _Context, *, member_id_mention_or_name: str) -> None:
        """
        Checks, if a given member exists on this guild.

        Usage:
          vivi check member [member_id_mention_or_name]

        Parameters:
          member_id_mention_or_name: Mandatory. The ID, a mention or the (nick) name of a member of this guild.

        Examples:
          vivi check member 1
          vivi check member @The worst.
          vivi check member The worst.
          vivi check member The worst.#1337
        """
        result = _utils.discord.get_member(ctx, member_id_mention_or_name)
        if result:
            await _utils.discord.reply(ctx, result.mention)
        else:
            lines = [
                f'This is not a valid member of this server:',
                member_id_mention_or_name
            ]
            await _utils.discord.reply_lines(ctx, lines)


    @_is_owner()
    @base.command(name='message')
    async def message(self, ctx: _Context, channel: _TextChannel, message_id: str) -> None:
        """
        Checks, if a message with the given ID exists in the given channel and can be accessed by the bot.

        Usage:
          vivi check message [channel] [message_id]

        Parameters:
          channel:    Mandatory. A channel name or mention of a channel on this guild.
          message_id: Mandatory. The ID of a message in the given channel.

        Examples:
          vivi check message #foobar 1
        """
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
    async def role(self, ctx: _Context, role_id_or_mention: str) -> None:
        """
        Checks, if a role with the given ID or mention exists on this guild and prints information about it.

        Usage:
          vivi check role [role_id_or_mention]

        Parameters:
          role_id_or_mention: Mandatory. The ID or a mention of a role on this guild.

        Exmaples:
          vivi check role 1
          vivi check role @foobar
        """
        result: _Role = _utils.discord.get_role(ctx, role_id_or_mention)
        if result:
            lines = [
                result.mention,
                f'Position: {result.position}',
                f'Is managed by a bot: {result.is_bot_managed()}',
                f'Is managed by an integration: {result.is_integration()}',
                f'Is everyone: {result.is_default()}',
                f'Is Nitro Booster: {result.is_premium_subscriber()}',
            ]
            await _utils.discord.reply_lines(ctx, lines)
        else:
            lines = [
                f'This is not a valid role:',
                role_id_or_mention,
            ]
            await _utils.discord.reply_lines(ctx, lines)


def setup(bot: _Bot):
    bot.add_cog(ChecksCog(bot))