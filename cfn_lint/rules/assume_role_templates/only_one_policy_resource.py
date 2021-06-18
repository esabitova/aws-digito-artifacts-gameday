from cfnlint.rules import CloudFormationLintRule
from cfn_lint.rules.common import match_only_resource


class OnlyOnePolicyResource(CloudFormationLintRule):
    """ Validate only one IAM Policy resource """
    id = 'E9003'
    shortdesc = 'Validate single resource of type AWS::IAM::Policy'
    description = 'Validate single resource of type AWS::IAM::Policy'
    source_url = ''
    tags = ['resources', 'iam']

    def match(self, cfn):
        return match_only_resource(cfn, 'AWS::IAM::Policy')
