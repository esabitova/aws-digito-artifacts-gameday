from cfnlint.rules import CloudFormationLintRule
from cfn_lint.rules.common import validate_no_property


class NoAlarmName(CloudFormationLintRule):
    """ Validate no AlarmName property for AWS::CloudWatch::Alarm resource """
    id = 'E9001'
    shortdesc = 'Validate that AlarmName is not set for CloudWatch alarms'
    description = 'Validate that AlarmName is not set for CloudWatch alarms'
    source_url = ''
    tags = ['resources', 'cloudwatch']

    def match(self, cfn):
        return validate_no_property(cfn, 'AWS::CloudWatch::Alarm', 'AlarmName')
