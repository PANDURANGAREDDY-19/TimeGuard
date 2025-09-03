from datetime import datetime, timezone, timedelta

# Indian Standard Time (GMT+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

def now_ist():
    """Get current datetime in IST"""
    return datetime.now(IST)

def utc_to_ist(utc_dt):
    """Convert UTC datetime to IST"""
    if utc_dt is None:
        return None
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    return utc_dt.astimezone(IST)

def ist_to_utc(ist_dt):
    """Convert IST datetime to UTC for database storage"""
    if ist_dt is None:
        return None
    if ist_dt.tzinfo is None:
        ist_dt = ist_dt.replace(tzinfo=IST)
    return ist_dt.astimezone(timezone.utc).replace(tzinfo=None)

def format_ist_datetime(dt, format_str='%Y-%m-%d %H:%M'):
    """Format datetime in IST"""
    if dt is None:
        return ''
    ist_dt = utc_to_ist(dt)
    return ist_dt.strftime(format_str)