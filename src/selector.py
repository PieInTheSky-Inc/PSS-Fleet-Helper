from typing import Callable as _Callable
from typing import Dict as _Dict
from typing import List as _List
from typing import Tuple as _Tuple

import asyncio as _asyncio
from discord import Message as _Message
from discord.ext.commands import Context as _Context

from pssapi import PssEntityBase as _PssEntityBase


# ---------- Classes ----------

class Selector():
    def __init__(self, ctx: _Context, search_term: str, available_options: _List[_PssEntityBase], short_text_function: _Callable[[_PssEntityBase], str], timeout: float = 60.0) -> None:
        self.__available_options: _List[_PssEntityBase] = list(available_options)
        self.__context: _Context = ctx
        self.__search_term: str = search_term
        self.__short_text_function: _Callable[[_PssEntityBase], str] = short_text_function
        self.__timeout: int = timeout
        self.__current_options: _Dict[str, _PssEntityBase] = {i: option for i, option in enumerate(self.__available_options, 1)}
        self.__message: _Message = None
        self.__title: str = Selector.__get_title(self.__search_term)


    async def wait_for_option_selection(self) -> _Tuple[bool, _Dict]:
        def option_selection_check(message: _Message) -> bool:
            if message.author == self.__context.author:
                return True
            return False


        await self.__post_options()

        reply: _Message = None

        while True:
            try:
                reply = await self.__context.bot.wait_for('message', timeout=self.__timeout, check=option_selection_check)
            except _asyncio.TimeoutError:
                await self.__message.edit('Selection cancelled')
                return False, {}
            else:
                if reply:
                    content = str(reply.content)
                    try:
                        selection = int(content)
                    except ValueError:
                        pass
                    else:
                        if selection in self.__current_options.keys():
                            return True, self.__current_options[selection]


    async def __post_options(self) -> None:
        options_display = await Selector.__get_options_display(self.__available_options, self.__short_text_function)
        content = f'{self.__title}```{options_display}```'
        if not self.__message:
            self.__message = await self.__context.reply(content, mention_author=False)


    @staticmethod
    async def __get_options_display(entities: _List[_PssEntityBase], short_text_function: _Callable[[_PssEntityBase], str]) -> str:
        options = []
        for i, entity in enumerate(entities, 1):
            number = str(i)
            short_text = short_text_function(entity)
            option = f'{number.rjust(2)}: {short_text}'
            options.append(option)
        return '\n'.join(options)


    @staticmethod
    def __get_title(search_term: str) -> str:
        result = 'Multiple matches found'
        if search_term:
            result += f' while searching for **{search_term}**'
        result += ':'
        return result