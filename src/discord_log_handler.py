import asyncio
import logging

import discord


class DiscordLogHandler(logging.Handler):
    def __init__(self, bot: discord.Bot, channel_id: int):
        super().__init__()
        self.bot = bot
        self.channel_id = channel_id

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

        channel = self.bot.get_channel(self.channel_id)
        if not channel:
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
