import os

DISCORD_BOT_TOKEN = os.environ.get('VIVIBOT_DISCORD_BOT_TOKEN')

THROW_COMMAND_ERRORS = bool(int(os.environ.get('THROW_COMMAND_ERRORS', 0)))

VERSION = '0.0.1'