import asyncio
import logging

import discord

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

    discord_handler = DiscordLogHandler(bot, error_channel_id)
    discord_handler.setLevel(logging.ERROR)
    discord_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(discord_handler)

    return logger


__all__ = [
    "setup_logging",
]
