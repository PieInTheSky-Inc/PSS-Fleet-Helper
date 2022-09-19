from datetime import datetime as _datetime


# ---------- Functions ----------

def date(date_time: _datetime, include_tz: bool = True, include_tz_brackets: bool = True) -> str:
    result = date_time.strftime('%Y-%m-%d')
    if include_tz:
        tz = date_time.strftime('%Z')
        if include_tz_brackets:
            result += ' ({})'.format(tz)
        else:
            result += ' {}'.format(tz)
    return result


def datetime(date_time: _datetime, include_time: bool = True, include_tz: bool = True, include_tz_brackets: bool = True) -> str:
    output_format = '%Y-%m-%d'
    if include_time:
        output_format += ' %H:%M:%S'
    if include_tz:
        if include_tz_brackets:
            output_format += ' (%Z)'
        else:
            output_format += ' %Z'
    result = date_time.strftime(output_format)
    return result