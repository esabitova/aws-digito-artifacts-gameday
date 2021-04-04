import logging
from datetime import datetime
from typing import Union


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _parse_recovery_date_time(restore_date_time_str: str, format: str) -> Union[datetime, None]:
    if restore_date_time_str.strip():
        try:
            return datetime.strptime(restore_date_time_str, format)
        except ValueError as ve:
            print(ve)
    return None


def parse_recovery_date_time(events: dict, context: dict) -> dict:
    """
    Tries to parses the given `RecoveryPointDateTime` and returns it back if success
    :return: The dictionary that indicates if latest availabe recovery point should be used
    """
    DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S%z"

    if 'RecoveryPointDateTime' not in events:
        raise KeyError('Requires ExecutionId')

    restore_date_time_str = events['RecoveryPointDateTime']
    restore_date_time = _parse_recovery_date_time(restore_date_time_str=restore_date_time_str,
                                                  format=DATETIME_FORMAT)
    if restore_date_time:
        return {
            'RecoveryPointDateTime': datetime.strftime(restore_date_time, DATETIME_FORMAT),
            'UseLatestRecoveryPoint': False
        }
    else:
        return {
            'RecoveryPointDateTime': 'None',
            'UseLatestRecoveryPoint': True
        }
