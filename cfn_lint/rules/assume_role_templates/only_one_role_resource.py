from cfnlint.rules import CloudFormationLintRule
from cfn_lint.rules.common import match_only_resource


class OnlyOneRoleResource(CloudFormationLintRule):
    """ Validate only one IAM Role resource """
    id = 'E9004'
    shortdesc = 'Validate single resource of type AWS::IAM::Role'
    description = 'Validate single resource of type AWS::IAM::Role'
    source_url = ''
    tags = ['resources', 'iam']

    def match(self, cfn):
        return match_only_resource(cfn, 'AWS::IAM::Role')
