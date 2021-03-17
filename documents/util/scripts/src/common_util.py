from datetime import datetime, timezone
from typing import List

from dateutil import parser


def start_time(events, context):
    return datetime.now(timezone.utc).isoformat()


def recovery_time(events, context):
    return (datetime.now(timezone.utc) - parser.parse(events['StartTime'])).seconds