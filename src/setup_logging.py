import asyncio
import logging

import discord

from . import bot_settings
from .discord_log_handler import DiscordLogHandler


def setup_logging(bot: discord.Bot, error_channel_id: int) -> logging.Logger:
    logger = logging.getLogger("pss_fleet_helper")
    logger.setLevel(logging.INFO)  # Capture INFO and above globally

    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if bot_settings.DISCORD_ERROR_LOG_GUILD_ID and bot_settings.DISCORD_ERROR_LOG_CHANNEL_ID:
        print(f"[setup_logging] Setting up Discord error logging. Guild ID: {bot_settings.DISCORD_ERROR_LOG_GUILD_ID}, Channel ID: {bot_settings.DISCORD_ERROR_LOG_CHANNEL_ID}")
        discord_handler = DiscordLogHandler(bot, bot_settings.DISCORD_ERROR_LOG_GUILD_ID, bot_settings.DISCORD_ERROR_LOG_CHANNEL_ID)
        discord_handler.setLevel(logging.ERROR)
        discord_handler.setFormatter(formatter)
        logger.addHandler(discord_handler)

    return logger


__all__ = [
    "setup_logging",
]
