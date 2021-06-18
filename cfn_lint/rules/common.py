from cfnlint.rules import RuleMatch


def validate_no_property(cfn, resource_type: str, property_name: str):
    matches = []
    resources = cfn.get_resources([resource_type])
    for resource_name, resource in resources.items():
        if property_name in resource.get('Properties'):
            path = ['Resources', resource_name]
            matches.append(RuleMatch(path, '{} not allowed for {} {}'
                                     .format(property_name, resource_type, resource_name)))
    return matches


def match_only_resource(cfn, resource_type: str):
    matches = []
    resources = cfn.get_resources([resource_type])
    if len(resources) != 1:
        matches.append(RuleMatch(cfn.filename, 'Expected [1] resource of type {}, but found [{}]'
                                 .format(resource_type, len(resources))))
    return matches
