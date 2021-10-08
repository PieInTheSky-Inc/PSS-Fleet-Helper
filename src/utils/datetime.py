from datetime import datetime as _datetime
from datetime import timezone as _timezone


# ---------- Functions ----------

def get_utc_now() -> _datetime:
    return _datetime.now(_timezone.utc)