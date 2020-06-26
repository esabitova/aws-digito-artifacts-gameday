import boto3
import json

INTERNET_DESTINATION = '0.0.0.0/0'

def get_existing_routes(events, context):
    ec2 = boto3.client('ec2')

    routeTableResponse = ec2.describe_route_tables(
        Filters=[{
            'Name': 'association.subnet-id',
            'Values': events['ApplicationSubnetIds']
        }])
    return {'ExistingRouteTableResponse': json.dumps(routeTableResponse)}

def route_through_appliance(events, context):
    ec2 = boto3.client('ec2')

    routeTableResponse = json.loads(events['ExistingRouteTableResponse'])

    for routeTable in routeTableResponse['RouteTables']:
        routeTableId = routeTable["RouteTableId"]

        for route in routeTable["Routes"]:
            if (route["DestinationCidrBlock"] == INTERNET_DESTINATION):
                 # Replace existing route from application subnet to internet gateway to point to appliance
                 ec2.replace_route(
                     DestinationCidrBlock = INTERNET_DESTINATION,
                     InstanceId = events['ApplianceInstanceId'],
                     RouteTableId = routeTableId
                 )
                 break

def cleanup_to_previous_route(events, context):
    ec2 = boto3.client('ec2')
    routeTableResponse = json.loads(events['ExistingRouteTableResponse'])

    for routeTable in routeTableResponse['RouteTables']:
        routeTableId = routeTable["RouteTableId"]

        for route in routeTable["Routes"]:
            if (route["DestinationCidrBlock"] == INTERNET_DESTINATION):
                # Replace existing route from application subnet to internet gateway to point to appliance
                if ('NatGatewayId' in route):
                    ec2.replace_route(
                        DestinationCidrBlock = INTERNET_DESTINATION,
                        NatGatewayId = route['NatGatewayId'],
                        RouteTableId = routeTableId
                    )
                elif ('GatewayId' in route):
                    ec2.replace_route(
                        DestinationCidrBlock = INTERNET_DESTINATION,
                        GatewayId = route['GatewayId'],
                        RouteTableId = routeTableId
                    )
                break