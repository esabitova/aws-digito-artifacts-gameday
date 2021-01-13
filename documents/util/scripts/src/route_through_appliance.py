import boto3
import json

INTERNET_DESTINATION = '0.0.0.0/0'


def get_existing_routes(events, context):
    ec2 = boto3.client('ec2')

    route_table_response = ec2.describe_route_tables(
        Filters=[{
            'Name': 'association.subnet-id',
            'Values': events['ApplicationSubnetIds']
        }])
    return {'ExistingRouteTableResponse': json.dumps(route_table_response)}


def route_through_appliance(events, context):
    ec2 = boto3.client('ec2')

    route_table_response = json.loads(events['ExistingRouteTableResponse'])

    for route_table in route_table_response['RouteTables']:
        route_table_id = route_table["RouteTableId"]

        for route in route_table["Routes"]:
            if route["DestinationCidrBlock"] == INTERNET_DESTINATION:
                # Replace existing route from application subnet to internet gateway to point to appliance
                ec2.replace_route(
                    DestinationCidrBlock=INTERNET_DESTINATION,
                    InstanceId=events['ApplianceInstanceId'],
                    RouteTableId=route_table_id
                )
                break


def cleanup_to_previous_route(events, context):
    ec2 = boto3.client('ec2')
    route_table_response = json.loads(events['ExistingRouteTableResponse'])

    for route_table in route_table_response['RouteTables']:
        route_table_id = route_table["RouteTableId"]

        for route in route_table["Routes"]:
            if route["DestinationCidrBlock"] == INTERNET_DESTINATION:
                # Replace existing route from application subnet to internet gateway to point to appliance
                if 'NatGatewayId' in route:
                    ec2.replace_route(
                        DestinationCidrBlock=INTERNET_DESTINATION,
                        NatGatewayId=route['NatGatewayId'],
                        RouteTableId=route_table_id
                    )
                elif 'GatewayId' in route:
                    ec2.replace_route(
                        DestinationCidrBlock=INTERNET_DESTINATION,
                        GatewayId=route['GatewayId'],
                        RouteTableId=route_table_id
                    )
                break
