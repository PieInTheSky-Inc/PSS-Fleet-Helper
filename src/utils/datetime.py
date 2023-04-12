from datetime import datetime as _datetime
from datetime import timezone as _timezone



# ---------- Constants ----------

UNIX_START_DATE: _datetime = _datetime(1970, 1, 1, tzinfo=_timezone.utc)




# ---------- Functions ----------

def get_unix_timestamp(dt: _datetime) -> int:
    result = int((dt - UNIX_START_DATE).total_seconds())
    return result


def get_utc_now() -> _datetime:
    return _datetime.now(_timezone.utc)


def utc_from_timestamp(date_string: str) -> _datetime:
    result = _datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S.%fZ')
    return result


def utc_to_timestamp(dt: _datetime) -> str:
    result = dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    return result