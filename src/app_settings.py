import os as _os


ACCESS_TOKEN: str = _os.environ.get('PSS_ACCESS_TOKEN')


DISCORD_BOT_CLIENT_ID: str = _os.environ.get('VIVIBOT_DISCORD_BOT_CLIENT_ID')
DISCORD_BOT_TOKEN: str = _os.environ.get('VIVIBOT_DISCORD_BOT_TOKEN')


THROW_COMMAND_ERRORS: bool = bool(int(_os.environ.get('THROW_COMMAND_ERRORS', 0)))


VERSION: str = '0.2.0'