from discord.ext.commands import Bot as _Bot
from discord.ext.commands import command as _command
from discord.ext.commands import group as _command_group
from discord.ext.commands import Context as _Context

from .cog_base import CogBase as _CogBase
from .. import bot_settings as _bot_settings
from .. import utils as _utils



class About(_CogBase):
    def __init__(self, bot: _Bot) -> None:
        super().__init__(bot)
        self.about_placeholders.help = self.about_placeholders.help.format(_utils.discord.PLACEHOLDERS.replace('`', ''))


    @_command_group(name='about', brief='General info about the bot', invoke_without_command=True)
    async def about(self, ctx: _Context) -> None:
        """
        Returns general information about this bot.

        Usage:
          vivi about
        """
        info = {
            'Server count': len(self.bot.guilds),
            'Member count': sum([guild.member_count for guild in self.bot.guilds]),
            'Version': _bot_settings.VERSION,
            'Github': '<https://github.com/PieInTheSky-Inc/PSS-Fleet-Helper>',
        }
        lines = [f'{key}: {value}' for key, value in info.items()]
        await _utils.discord.reply_lines(ctx, lines)


    @about.command(name='placeholders', aliases=['substitutions', 'sub'], brief='List available placeholders', )
    async def about_placeholders(self, ctx: _Context) -> None:
        """
        Available placeholders:
        {}
        """
        await ctx.send_help('about placeholders')


    @_command(name='invite', brief='Produce invite link')
    async def cmd_invite(self, ctx: _Context) -> None:
        """
        Produces a link to invite this bot to your server.

        Usage:
          vivi invite
        """
        invite_link = f'https://discordapp.com/oauth2/authorize?scope=bot%20applications.commands&permissions=476674780370&client_id={_bot_settings.DISCORD_BOT_CLIENT_ID}'
        await _utils.discord.reply(ctx, invite_link)


def setup(bot: _Bot):
    bot.add_cog(About(bot))