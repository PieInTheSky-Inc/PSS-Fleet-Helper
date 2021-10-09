import os



DATABASE_SSL_MODE: str = os.environ.get('DATABASE_SSL_MODE', 'require')
DATABASE_URL: str = f'{os.environ.get("DATABASE_URL")}?sslmode={DATABASE_SSL_MODE}'

DISCORD_BOT_TOKEN: str = os.environ.get('VIVIBOT_DISCORD_BOT_TOKEN')


PRINT_DEBUG_DB: bool = bool(int(os.environ.get('PRINT_DEBUG_DB', '0')))

PSS_ACCESS_TOKEN: str = os.environ.get('PSS_ACCESS_TOKEN')


THROW_COMMAND_ERRORS: bool = bool(int(os.environ.get('THROW_COMMAND_ERRORS', 0)))


VERSION: str = '0.0.1'