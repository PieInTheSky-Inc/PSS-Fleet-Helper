import asyncio

import discord
import pssapi

from src import utils

from .pss_chat_logger import PssChatListener


class PssDiscordListener(PssChatListener):
    def __init__(self, discord_bot: discord.Bot, webhook: discord.Webhook):
        super().__init__(str(webhook.id))
        self.discord_bot = discord_bot
        self.webhook = webhook

    def on_message(self, message: pssapi.entities.Message) -> None:
        asyncio.run(self._post_to_webhook(message))

    async def _post_to_webhook(self, message: pssapi.entities.Message) -> None:
        content = PssDiscordListener._make_discord_message_content(message)
        avatar_url = self.discord_bot.user.display_avatar.url if self.discord_bot.user else None

        username = f"PSS Chat Logger ({self.webhook.name})"
        try:
            await self.webhook.send(content=content, username=username, avatar_url=avatar_url)
        except (discord.errors.HTTPException, discord.errors.Forbidden):
            print(f"[log_message] Failed to send message with ID {message.message_id} for chat logger '{self.webhook.name}' (ID: {self.webhook.id}).")

    @staticmethod
    def _make_discord_message_content(message: pssapi.entities.Message) -> str:
        discord_message = f"**{utils.discord.escape_markdown_and_mentions(message.user_name)}"
        if message.alliance_name:
            discord_message += f"** ({utils.discord.escape_markdown_and_mentions(message.alliance_name)})**"

        return discord_message


__all__ = [
    "PssDiscordListener",
]
