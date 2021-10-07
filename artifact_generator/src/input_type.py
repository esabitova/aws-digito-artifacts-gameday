from enum import Enum
from artifact_generator.src import constants


class InputType(Enum):
    """
    Enumeration for artifact generator inputs
    """
    SERVICE = ('Enter service name(ex - api-gw)', 'service')
    TYPE = ('Is this a test or a sop (test/sop)?', 'type')
    NAME = ('Enter short name of test/sop (ex - restore_from_backup)', 'name')
    FULL_NAME = ('Enter full document name in format <Action><Service><SomeDescription> '
                 '(ex - RestoreDynamoDBTableFromBackup)', 'fullName')
    DISPLAY_NAME = ('Enter display name', 'displayName')
    DATE = ('Enter date in YYYY-MM-DD format if in the past, else we default to current date', 'date')
    DESCRIPTION = ('Enter description', 'description')
    RESOURCE_ID = ('Enter a name for the primary resource ID input parameter (ex: QueueUrl, DatabaseIdentifier)',
                   'primaryResourceId')
    FAILURE_TYPE = ('Enter failure type(s) as a comma-separated list (one or more of {})'
                    .format(','.join(constants.FAILURE_TYPES)), 'failureType')
    RISK = ('Enter risk ({})'.format('/'.join(constants.RISKS)), 'risk')
    CFN_TEMPLATE = ('Enter the name of the cloudformation template for testing the test/sop '
                    '(ex: SqsTemplate, RdsTemplate)', 'cfnTemplateName')
    CFN_RESOURCE_OUTPUT = ('Enter the name of the cloudformation output for the primary resource ID',
                           'cfnPrimaryResourceOutput')
    SUPPORTS_ROLLBACK = ('Does test support rollback (yes/no)?', 'supportsRollback', 'Applicable to tests only')
    ALARM_PREFIX = ('Enter alarm name prefix - this will appear in the automation input as '
                    '<Prefix>AlarmName (ex: CpuUtilizationAlarmName)', 'alarmPrefix', 'Applicable to tests only')
    CFN_ALARM_OUTPUT = ('Enter the name of the cloudformation output for the alarm', 'cfnAlarmOutput',
                        'Applicable to tests only')
    ALARM_ID = ('Enter ID for recommended alarm (ex - compute:alarm:asg-cpu-util:2020-07-13)', 'alarmId',
                'Applicable to tests that support recommended alarms only')
    SUPPORTS_RECOVERY_POINT = ('Does sop calculate recovery point (yes/no)?', 'supportsRecoveryPoint',
                               'Applicable to SOPs only')
    RECOVERY_POINT_STEP = ('Enter name of the automation document step that calculates recovery point '
                           '(ex: GetRecoveryPoint)', 'recoveryPointStep',
                           'Applicable to SOPs that calculate recovery point only')

    def __init__(self, prompt: str, override_key: str, additional_info: str = None):
        self.prompt = prompt
        self.override_key = override_key
        self.additional_info = additional_info
