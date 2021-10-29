from datetime import datetime as _datetime
from datetime import timezone as _timezone



# ---------- Constants ----------





# ---------- Functions ----------

def get_utc_now() -> _datetime:
    return _datetime.now(_timezone.utc)


def utc_from_timestamp(date_string: str) -> _datetime:
    result = _datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S.%fZ')
    return result


def utc_to_timestamp(dt: _datetime) -> str:
    result = dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    return result