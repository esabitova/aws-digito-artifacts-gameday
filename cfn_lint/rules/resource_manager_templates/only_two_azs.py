from cfnlint.rules import CloudFormationLintRule
from cfnlint.rules import RuleMatch


class OnlyTwoAZs(CloudFormationLintRule):
    """ Validate no getting 3rd and next AZs in select """
    id = 'E9007'
    shortdesc = 'Validate that only two AZs are used'
    description = 'Validate that only two AZs are used'
    source_url = ''
    tags = ['resources', 'subnet', 'az']

    def match(self, cfn):
        matches = []
        property_name = 'AvailabilityZone'
        resource_type = 'AWS::EC2::Subnet'
        resources = cfn.get_resources([resource_type])
        for resource_name, resource in resources.items():
            properties = resource.get('Properties')
            if property_name in properties:
                availability_zone = properties[property_name]
                if availability_zone.get('Fn::Select') and availability_zone.get('Fn::Select')[0] > 1:
                    path = ['Resources', resource_name]
                    matches.append(RuleMatch(path, '{} can be set by only first two AZs for {} {}'
                                             .format(property_name, resource_type, resource_name)))
        return matches
