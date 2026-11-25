import asyncio
import logging

import discord


class DiscordLogHandler(logging.Handler):
    def __init__(self, bot: discord.Bot, guild_id: int, channel_id: int):
        super().__init__()
        self.bot = bot
        self.channel_id = channel_id
        self.guild_id = guild_id

    def emit(self, record: logging.LogRecord):
        # Prevent infinite loops if Discord itself throws an error while logging
        if record.name.startswith("discord"):
            return

        # Format the log message (includes timestamp, level, message, and traceback)
        log_entry = self.format(record)

        # Schedule the async send on the bot's running event loop
        if self.bot.loop and self.bot.loop.is_running():
            self.bot.loop.create_task(self._send_to_discord(log_entry))

    async def _send_to_discord(self, message: str):
        # Wait until the bot's internal cache is ready so get_channel() works
        await self.bot.wait_until_ready()

        guild = self.bot.get_guild(self.guild_id) or await self.bot.fetch_guild(self.guild_id)
        if not guild:
            print(f"[DiscordLogHandler] Could not get/fetch guild with id '{self.guild_id}'.")
            return

        channel = guild.get_channel(self.channel_id) or await guild.fetch_guild(self.guild_id)
        if not channel:
            print(f"[DiscordLogHandler] Could not get/fetch channel with id '{self.channel_id}' on guild '{guild.name}' (ID: {guild.id}).")
            return

        # Truncate to stay safely within Discord's 2000-character message limit
        messages = []
        while len(message) > 1900:
            messages.append(message[:1900])
            message = message[:1900]
        messages.append(message)

        try:
            for msg in messages:
                await channel.send(f"```py\n{msg}\n```")
        except Exception:
            # Fallback so a failed Discord API call doesn't crash the logger
            pass

__all__ = [
    "DiscordLogHandler",
]
