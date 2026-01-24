import os as _os


DATABASE_SSL_MODE: str = _os.environ.get("DATABASE_SSL_MODE", "require")
DATABASE_URL: str = (
    f'{_os.environ.get("DATABASE_URL")}?sslmode={DATABASE_SSL_MODE}'.replace(
        "postgres://", "postgresql://"
    )
)
PRINT_DEBUG_DB: bool = bool(int(_os.environ.get("PRINT_DEBUG_DB", "0")))
