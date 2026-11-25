import json as _json
import os as _os


AUTHORIZED_CHANNEL_IDS: list[int] = _json.loads(_os.environ.get("AUTHORIZED_CHANNEL_IDS", "[]"))


COGS_BASE_PATH: str = "src.cogs"
COGS_TO_LOAD: dict[str, str] = {
    "About": f"{COGS_BASE_PATH}.about",
    "ChatLogger": f"{COGS_BASE_PATH}.chatlogger",
    "Fleets": f"{COGS_BASE_PATH}.fleet",
    "RoleManagement": f"{COGS_BASE_PATH}.rolemanagement",
    "ReactionRoles": f"{COGS_BASE_PATH}.reactionroles",
    "Utility": f"{COGS_BASE_PATH}.utility",
}


DISCORD_BOT_CLIENT_ID: str = _os.environ.get(
    "VIVIBOT_DISCORD_BOT_CLIENT_ID",
    _os.environ.get("FLEETHELPER_DISCORD_BOT_CLIENT_ID"),
)
DISCORD_BOT_TOKEN: str = _os.environ.get("VIVIBOT_DISCORD_BOT_TOKEN", _os.environ.get("FLEETHELPER_DISCORD_BOT_TOKEN"))
_DISCORD_ERROR_LOG_CHANNEL: str | None = _os.environ.get("DISCORD_ERROR_LOG_CHANNEL")
DISCORD_ERROR_LOG_GUILD_ID: int = _DISCORD_ERROR_LOG_CHANNEL.split("/")[0] if _DISCORD_ERROR_LOG_CHANNEL and "/" in _DISCORD_ERROR_LOG_CHANNEL else None
DISCORD_ERROR_LOG_CHANNEL_ID: int = _DISCORD_ERROR_LOG_CHANNEL.split("/")[1] if _DISCORD_ERROR_LOG_CHANNEL and "/" in _DISCORD_ERROR_LOG_CHANNEL else None


DEFAULT_PREFIXES: list[str] = [
    "fh ",
    "vivi ",
    "vv ",
]

PRIVILEGED_INTENTS: dict[str, bool] = _json.loads(_os.environ.get("PRIVILEGED_INTENTS", '{"presence": true, "members": true, "messages": true}'))
INTENT_PRESENCE: bool = PRIVILEGED_INTENTS.get("presence", True)
INTENT_MEMBERS: bool = PRIVILEGED_INTENTS.get("members", True)
INTENT_MESSAGES: bool = PRIVILEGED_INTENTS.get("messages", True)


PSS_ACCESS_TOKEN: str | None = _os.environ.get("PSS_ACCESS_TOKEN", _os.environ.get("PSSAPI_PUBLIC_ACCESS_TOKEN"))
PSS_USER_ID: int = int(_os.environ.get("PSS_USER_ID", 0))


THROW_COMMAND_ERRORS: bool = bool(int(_os.environ.get("THROW_COMMAND_ERRORS", 0)))


VERSION: str = "0.11.0"
