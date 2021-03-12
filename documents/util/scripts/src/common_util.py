from datetime import datetime, timezone
from typing import List

from dateutil import parser


def start_time(events, context):
    return datetime.now(timezone.utc).isoformat()


def recovery_time(events, context):
    return (datetime.now(timezone.utc) - parser.parse(events['StartTime'])).seconds


def remove_substrings(events: dict, context: dict) -> dict:
    if 'StringToEdit' not in events or 'SubstringsToRemove' not in events:
        raise KeyError('Requires SubstringsToRemove and StringToEdit in events')

    string_to_edit: str = events['StringToEdit']
    substrings_to_remove: List = events['SubstringsToRemove']

    for substring in substrings_to_remove:
        string_to_edit = string_to_edit.replace(substring, "")

    return {'ResultString': string_to_edit}
