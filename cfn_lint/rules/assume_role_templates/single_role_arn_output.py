from cfnlint.rules import CloudFormationLintRule
from cfnlint.rules import RuleMatch


class SingleRoleArnOutput(CloudFormationLintRule):
    """ Validate CloudFormation template has a single output referencing an IAM Role ARN """
    id = 'E9005'
    shortdesc = 'Validate single IAM Role Arn output'
    description = 'Validate single IAM Role Arn output'
    source_url = ''
    tags = ['outputs', 'iam']

    def match(self, cfn):
        matches = []
        outputs = cfn.template.get('Outputs', {})
        if len(outputs) != 1:
            matches.append(RuleMatch(cfn.filename, 'Expected [1] output but found [{}]'.format(len(outputs))))
        else:
            output = outputs.popitem()
            value = output[1].get('Value', {})
            if value:
                match = RuleMatch(['Outputs', output[0]],
                                  'Invalid output {}. Expected output value to be a IAM Role ARN'.format(output[0]))
                # We continue matching only if value is present. If not E6002 would be thrown.
                attribute_ref = value.get('Fn::GetAtt', '')
                if not attribute_ref:
                    matches.append(match)
                else:
                    attribute = attribute_ref.split('.')
                    if len(attribute) != 2 or attribute[1] != 'Arn':
                        matches.append(match)
                    else:
                        output_resource_name = attribute[0]
                        resources = cfn.get_resources()
                        for resource_name, resource in resources.items():
                            if resource_name == output_resource_name and resource.get('Type') != 'AWS::IAM::Role':
                                matches.append(match)
        return matches
