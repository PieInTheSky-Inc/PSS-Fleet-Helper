import asyncio as _asyncio
from typing import Dict as _Dict

import discord as _discord
from discord.ext import commands as _commands


# ---------- Classes ----------

class Confirmator():
    reactions: _Dict[str, bool] = {'✅': True, '❌': False}

    def __init__(self, ctx: _commands.Context, confirmation_message: str) -> None:
        self.__context: _commands.Context = ctx
        self.__confirmation_message: str = confirmation_message
        self.__reply: _discord.Message = None


    async def wait_for_option_selection(self) -> bool:
        def emoji_selection_check(reaction: _discord.Reaction, user: _discord.User) -> bool:
            if user != self.__context.bot.user:
                emoji = str(reaction.emoji)
                if (emoji in Confirmator.reactions.keys() and self.__reply.id == reaction.message.id):
                    return True
            return False

        await self.__post_confirmation_message()

        try:
            reaction, _ = await self.__context.bot.wait_for('reaction_add', timeout=60.0, check=emoji_selection_check)
        except _asyncio.TimeoutError:
            reaction = None


        if reaction:
            result = Confirmator.reactions[str(reaction.emoji)]
        else:
            result = False

        if result:
            try:
                await self.__reply.delete()
            except _discord.errors.NotFound:
                pass
        else:
            await self.__reply.edit('Command cancelled')

        return result


    async def __post_confirmation_message(self) -> _discord.Message:
        self.__reply = await self.__context.reply(f'{self.__confirmation_message}\n\nDo you want to proceed?', mention_author=False)
        for reaction in Confirmator.reactions.keys():
            await self.__reply.add_reaction(reaction)