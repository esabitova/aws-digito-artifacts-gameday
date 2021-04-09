from enum import unique, Enum


@unique
class LambdaInvocationType(Enum):
    RequestResponse = 1,
    Event = 2
