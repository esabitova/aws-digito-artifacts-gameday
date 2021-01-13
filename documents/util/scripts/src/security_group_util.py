import boto3


def allow_access_to_self(events, context):
    ec2 = boto3.client('ec2')

    if 'AccountId' not in events or 'SecurityGroupId' not in events:
        raise KeyError('Requires AccountId, SecurityGroupId in events')

    security_groups = ec2.describe_security_groups(GroupIds=[events['SecurityGroupId']])

    for ip_permission in security_groups['SecurityGroups'][0]['IpPermissions']:
        for user_id_group_pair in ip_permission['UserIdGroupPairs']:
            # Check for self security group present
            if user_id_group_pair['GroupId'] == events['SecurityGroupId'] and ip_permission['IpProtocol'] == "-1":
                return

    # Could not find rule to authorize access to self, adding a rule
    ec2.authorize_security_group_ingress(
        GroupId=events['SecurityGroupId'],
        IpPermissions=[{
            'IpProtocol': '-1',
            'UserIdGroupPairs': [{
                'GroupId': events['SecurityGroupId'],
                'UserId': events['AccountId']
            }]
        }]
    )
