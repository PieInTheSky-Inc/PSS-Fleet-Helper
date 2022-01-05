from datetime import datetime as _datetime
from datetime import timezone as _timezone

from . import settings as _settings


# ---------- Functions ----------

def format_pss_timestamp(timestamp: _datetime) -> str:
    result = timestamp.strftime(_settings.TIMESTAMP_FORMAT_PSS)
    return result


def get_utc_now() -> _datetime:
    return _datetime.now(_timezone.utc)
