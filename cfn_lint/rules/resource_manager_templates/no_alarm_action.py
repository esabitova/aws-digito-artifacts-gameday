from cfnlint.rules import CloudFormationLintRule
from cfn_lint.rules.common import validate_no_property


class NoAlarmAction(CloudFormationLintRule):
    """ Validate no AlarmActions property for AWS::CloudWatch::Alarm resource """
    id = 'E9000'
    shortdesc = 'Validate that AlarmActions is not set for CloudWatch alarms'
    description = 'Validate that AlarmActions is not set for CloudWatch alarms'
    source_url = ''
    tags = ['resources', 'cloudwatch']

    def match(self, cfn):
        return validate_no_property(cfn, 'AWS::CloudWatch::Alarm', 'AlarmActions')
