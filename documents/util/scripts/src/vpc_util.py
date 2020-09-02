import boto3

INTERNET_DESTINATION = '0.0.0.0/0'

def get_public_subnet_in_private_subnet_vpc(events, context):
    ec2 = boto3.client('ec2')

    subnet = ec2.describe_subnets(
        SubnetIds=[events['SubnetIds'][0]]
        )
    subnet_vpc_id = subnet['Subnets'][0]['VpcId']

    routeTableResponse = ec2.describe_route_tables(
        Filters=[{
            'Name': 'vpc-id',
            'Values': [subnet_vpc_id]
        }])

    for routeTable in routeTableResponse['RouteTables']:
        routeTableId = routeTable["RouteTableId"]

        for route in routeTable["Routes"]:
            if (route["DestinationCidrBlock"] == INTERNET_DESTINATION and 'GatewayId' in route):
                 for association in routeTable["Associations"]:
                     if ('SubnetId' in association):
                         output = {}
                         output['PublicSubnetId'] = association['SubnetId']
                         return output

    # Could not find public subnet in vpc
    raise Exception('Can not find public subnet id in vpc for subnet id %', events['SubnetId'])