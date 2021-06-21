from cfnlint.rules import CloudFormationLintRule
from cfnlint.rules import RuleMatch


class OnlyOneAlarmResource(CloudFormationLintRule):
    """ Validate only one CloudWatch alarm resource with Id ${AlarmLogicalId} """
    id = 'E9002'
    shortdesc = 'Validate single resource of type AWS::CloudWatch::Alarm and logical Id ${AlarmLogicalId}'
    description = 'Validate single resource of type AWS::CloudWatch::Alarm and logical Id ${AlarmLogicalId}'
    source_url = ''
    tags = ['resources', 'cloudwatch']

    def match(self, cfn):
        matches = []
        resources = cfn.get_resources(['AWS::CloudWatch::Alarm'])
        if len(resources) != 1:
            matches.append(RuleMatch(cfn.filename,
                                     'Expected [1] resource of type AWS::CloudWatch::Alarm, but found [{}]'
                                     .format(len(resources))))
        else:
            resource_name = resources.popitem()[0]
            if resource_name != '${AlarmLogicalId}':
                matches.append(RuleMatch(['Resources', resource_name],
                                         'Expected logical Id ${AlarmLogicalId}, but found ' + resource_name))
        return matches
