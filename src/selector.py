from typing import Any as _Any
from typing import Callable as _Callable
from typing import Dict as _Dict
from typing import Generic as _Generic
from typing import List as _List
from typing import Optional as _Optional
from typing import Tuple as _Tuple
from typing import TypeVar as _TypeVar
from typing import Union as _Union

import asyncio as _asyncio
from discord import Message as _Message
from discord.ext.commands import Context as _Context

T = _TypeVar('T')


# ---------- Classes ----------

class Selector(_Generic[T]):
    def __init__(self, ctx: _Context, search_term: str, available_options: _Union[_List[T], _Dict[_Any, T]], short_text_function: _Optional[_Callable[[T], str]] = None, title: _Optional[str] = None, timeout: float = 60.0) -> None:
        self.__got_options_dict: bool = isinstance(available_options, dict)
        self.__available_options: _Union[_List[T], _Dict[_Any, T]] = dict(available_options) if self.__got_options_dict else list(available_options)
        self.__context: _Context = ctx
        self.__search_term: str = search_term
        self.__short_text_function: _Callable[[T], str] = short_text_function
        self.__timeout: int = timeout
        self.__current_options: _Dict[_Any, T] = self.__available_options if self.__got_options_dict else {i: option for i, option in enumerate(self.__available_options, 1)}
        self.__message: _Message = None
        self.__title: str = title or Selector.__get_title(self.__search_term)


    async def wait_for_option_selection(self) -> _Tuple[bool, T]:
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
                    if content.strip().lower() == 'abort':
                        await self.__message.delete()
                        return True, None

                    try:
                        selection = int(content)
                    except ValueError:
                        pass
                    else:
                        if selection in self.__current_options.keys():
                            await self.__message.delete()
                            return True, self.__current_options[selection]


    async def __post_options(self) -> None:
        options_display = await Selector.__get_options_display(self.__available_options, self.__short_text_function)
        content = f'{self.__title}```{options_display}```'
        if not self.__message:
            self.__message = await self.__context.reply(content, mention_author=False)


    @staticmethod
    async def __get_options_display(options: _List[T], short_text_function: _Callable[[T], str]) -> str:
        lines = []
        for i, option in enumerate(options, 1):
            number = str(i)
            if short_text_function:
                short_text = short_text_function(option)
            else:
                short_text = str(option)
            line = f'{number.rjust(2)}: {short_text}'
            lines.append(line)
        return '\n'.join(lines)


    @staticmethod
    def __get_title(search_term: str) -> str:
        if search_term:
            result = 'Multiple matches found'
            result += f' while searching for **{search_term}**'
        else:
            result = 'Please choose'
        result += ' (type \'abort\' to abort):'
        return result