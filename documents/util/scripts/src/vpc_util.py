import boto3
from botocore.config import Config

INTERNET_DESTINATION = '0.0.0.0/0'


def get_public_subnet_in_private_subnet_vpc(events, context):
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    ec2 = boto3.client('ec2', config=config)

    subnet = ec2.describe_subnets(SubnetIds=[events['SubnetIds'][0]])
    subnet_vpc_id = subnet['Subnets'][0]['VpcId']

    route_table_response = ec2.describe_route_tables(
        Filters=[{
            'Name': 'vpc-id',
            'Values': [subnet_vpc_id]
        }])

    for route_table in route_table_response['RouteTables']:
        for route in route_table["Routes"]:
            if route["DestinationCidrBlock"] == INTERNET_DESTINATION and 'GatewayId' in route:
                for association in route_table["Associations"]:
                    if 'SubnetId' in association:
                        output = {}
                        output['PublicSubnetId'] = association['SubnetId']
                        return output

    # Could not find public subnet in vpc
    raise Exception('Can not find public subnet id in vpc for subnet id %', events['SubnetId'])
