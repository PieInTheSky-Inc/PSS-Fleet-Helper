import os as _os
import json as _json
from typing import List as _List



AUTHORIZED_CHANNEL_IDS: _List[int] = _json.loads(_os.environ.get('AUTHORIZED_CHANNEL_IDS', '[]'))


DISCORD_BOT_CLIENT_ID: str = _os.environ.get('VIVIBOT_DISCORD_BOT_CLIENT_ID')
DISCORD_BOT_TOKEN: str = _os.environ.get('VIVIBOT_DISCORD_BOT_TOKEN')


PREFIXES: _List[str] = [
    'vivi ',
    'vv '
]


THROW_COMMAND_ERRORS: bool = bool(int(_os.environ.get('THROW_COMMAND_ERRORS', 0)))


VERSION: str = '0.4.10'
