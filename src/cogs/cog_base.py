from discord.ext.commands import Cog as _Cog

from .. import model as _model


class CogBase(_Cog):
    def __init__(self, bot: _model.PssApiDiscordBot) -> None:
        if not bot:
            raise ValueError("Parameter 'bot' must not be None.")
        self.__bot = bot

    @property
    def bot(self) -> _model.PssApiDiscordBot:
        return self.__bot
