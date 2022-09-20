from discord.ext.commands import Bot as _Bot
from discord.ext.commands import Cog as _Cog

from .. import utils as _utils



class CogBase(_Cog):
    def __init__(self, bot: _Bot) -> None:
        if not bot:
            raise ValueError('Parameter \'bot\' must not be None.')
        self.__bot = bot


    @property
    def bot(self) -> _Bot:
        return self.__bot