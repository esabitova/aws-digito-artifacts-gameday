from enum import Enum


class AlarmState(Enum):
    OK = 1,
    ALARM = 2,
    INSUFFICIENT_DATA = 3
