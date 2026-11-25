import asyncio
import logging

import discord
import pssapi

from src import utils

from .pss_chat_logger import PssChatListenerAsync

LOGGER = logging.getLogger("pss_fleet_helper.PssDiscordListener")


class PssDiscordListener(PssChatListenerAsync):
    def __init__(self, discord_bot: discord.Bot, webhook: discord.Webhook):
        super().__init__(webhook.url)
        self.discord_bot = discord_bot
        self.webhook = webhook

    async def on_message(self, message: pssapi.entities.Message) -> None:
        content = PssDiscordListener._make_discord_message_content(message)
        avatar_url = self.discord_bot.user.display_avatar.url if self.discord_bot.user else None
        username = f"PSS Chat Logger ({self.webhook.name})"

        if self.discord_bot.loop and self.discord_bot.loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self._send_safe(content, username, avatar_url, message.message_id),
                self.discord_bot.loop,
            )
        else:
            await self._send_safe(content, username, avatar_url, message.message_id)

    async def _send_safe(self, content: str, username: str, avatar_url: str | None, message_id: int) -> None:
        try:
            await self.webhook.send(content=content, username=username, avatar_url=avatar_url)
        except (discord.errors.HTTPException, discord.errors.Forbidden):
            LOGGER.error(f"Failed to send message with ID {message_id} for chat logger '{self.webhook.name}' on guild '{webhook.guild.name}' (ID: {self.webhook.id})"

    @staticmethod
    def _make_discord_message_content(message: pssapi.entities.Message) -> str:
        discord_message = f"**{utils.discord.escape_markdown_and_mentions(message.user_name)}"
        if message.alliance_name:
            discord_message += f"** ({utils.discord.escape_markdown_and_mentions(message.alliance_name)})**"

        discord_message += f":** {utils.discord.escape_markdown_and_mentions(message.message)}"

        return discord_message


__all__ = [
    "PssDiscordListener",
]
