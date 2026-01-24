from datetime import datetime as _datetime
from datetime import timezone as _timezone


# ---------- Functions ----------


def formatted_datetime(
    date_time: str,
    include_time: bool = True,
    include_tz: bool = True,
    include_tz_brackets: bool = True,
) -> _datetime:
    format_string = "%Y-%m-%d"
    if include_time:
        format_string += " %H:%M:%S"
    if include_tz:
        if include_tz_brackets:
            format_string += " (%Z)"
        else:
            format_string += " %Z"
    result = _datetime.strptime(date_time, format_string)
    if result.tzinfo is None:
        result = result.replace(tzinfo=_timezone.utc)
    return result
