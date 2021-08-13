from cfnlint.rules import CloudFormationLintRule
from cfnlint.rules import RuleMatch


class HasConditionKey(CloudFormationLintRule):
    """ Validate only one IAM Policy resource """
    id = 'E9006'
    shortdesc = 'Validate condition key for IAM actions'
    description = 'Validate condition key for IAM actions'
    source_url = ''
    tags = ['resources', 'iam']
    kms_actions = ['kms:GenerateDataKey', 'kms:Decrypt', 'kms:Encrypt', 'kms:CreateGrant']

    def match(self, cfn):
        matches = []
        resources = cfn.get_resources(['AWS::IAM::Policy'])
        for resource_name, resource in resources.items():
            stmts = resource.get('Properties', {}).get('PolicyDocument', {}).get('Statement', [])
            matches.extend(self.__match_condition_key(resource_name, stmts,
                                                      ['kms:GenerateDataKey', 'kms:Decrypt', 'kms:Encrypt'],
                                                      'StringLike', 'kms:ViaService'))
            matches.extend(self.__match_condition_key(resource_name, stmts,
                                                      ['iam:PassRole'],
                                                      'StringEquals', 'iam:PassedToService'))
        return matches

    def __match_condition_key(self, resource_name: str, stmts: list, offending_actions: list,
                              expected_condition: str, expected_condition_key: str):
        matches = []
        for stmt in stmts:
            actions = [a for a in stmt.get('Action', []) if a in offending_actions]
            if actions and stmt.get('Resource', '') == '*':
                kms_via_service = stmt.get('Condition', {}).get(expected_condition, {}).get(expected_condition_key, '')
                if not kms_via_service:
                    path = ['Resources', resource_name]
                    matches.append(RuleMatch(path, 'Expected {} condition on {} condition key '
                                                   'when using action(s) {} with resource "*"'
                                             .format(expected_condition, expected_condition_key, actions)))
        return matches
