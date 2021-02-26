def start_time():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()

def recovery_time(events):
    from datetime import datetime, timezone
    from dateutil import parser
    return (datetime.now(timezone.utc) - parser.parse(events['StartTime'])).seconds