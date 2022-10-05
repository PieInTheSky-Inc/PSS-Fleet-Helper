import os as _os
import json as _json
from typing import Dict as _Dict
from typing import List as _List



AUTHORIZED_CHANNEL_IDS: _List[int] = _json.loads(_os.environ.get('AUTHORIZED_CHANNEL_IDS', '[]'))


COGS_BASE_PATH: str = 'src.cogs'
COGS_TO_LOAD: _Dict[str, str] = {
    'About': f'{COGS_BASE_PATH}.about',
    'ChatLogger': f'{COGS_BASE_PATH}.chatlogger',
    'RoleManagement': f'{COGS_BASE_PATH}.rolemanagement',
    'ReactionRoles': f'{COGS_BASE_PATH}.reactionroles',
    'Utility': f'{COGS_BASE_PATH}.utility',
}


DISCORD_BOT_CLIENT_ID: str = _os.environ.get('VIVIBOT_DISCORD_BOT_CLIENT_ID')
DISCORD_BOT_TOKEN: str = _os.environ.get('VIVIBOT_DISCORD_BOT_TOKEN')


DEFAULT_PREFIXES: _List[str] = [
    'vivi ',
    'vv '
]


THROW_COMMAND_ERRORS: bool = bool(int(_os.environ.get('THROW_COMMAND_ERRORS', 0)))


VERSION: str = '0.6.7'
