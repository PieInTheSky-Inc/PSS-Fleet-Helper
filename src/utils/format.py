from datetime import datetime as _datetime

from . import settings as _settings



def pss_timestamp(timestamp: _datetime) -> str:
    result = timestamp.strftime(_settings.TIMESTAMP_FORMAT_PSS)
    return result