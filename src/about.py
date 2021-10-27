from discord.ext.commands import Bot as _Bot
from discord.ext.commands import Cog as _Cog
from discord.ext.commands import command as _command
from discord.ext.commands import Context as _Context

import app_settings as _app_settings



class AboutCog(_Cog):
    def __init__(self, bot: _Bot) -> None:
        self.__bot = bot


    @property
    def bot(self) -> _Bot:
        return self.__bot


    @_command(name='about', brief='General info about the bot')
    async def cmd_about(self, ctx: _Context) -> None:
        info = {
            'Server count': len(self.bot.guilds),
            'Member count': sum([guild.member_count for guild in self.bot.guilds]),
            'Version': _app_settings.VERSION,
            'Github': '<https://github.com/PieInTheSky-Inc/ViViBot>',
        }
        await ctx.reply('\n'.join([f'{key}: {value}' for key, value in info.items()]), mention_author=False)


    @_command(name='invite', brief='Produce invite link')
    async def cmd_invite(self, ctx: _Context) -> None:
        await ctx.reply(f'https://discordapp.com/oauth2/authorize?scope=bot&permissions=139519798336&client_id={_app_settings.DISCORD_BOT_CLIENT_ID}', mention_author=False)


def setup(bot: _Bot):
    bot.add_cog(AboutCog(bot))