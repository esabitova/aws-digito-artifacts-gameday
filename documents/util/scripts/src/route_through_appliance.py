import json
import logging
import time
from typing import List

import boto3
from botocore.config import Config

INTERNET_DESTINATION = '0.0.0.0/0'


def get_existing_routes(events, context):
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    ec2 = boto3.client('ec2', config=config)

    route_table_response = ec2.describe_route_tables(
        Filters=[{
            'Name': 'association.subnet-id',
            'Values': events['ApplicationSubnetIds']
        }])
    return {'ExistingRouteTableResponse': json.dumps(route_table_response)}


def route_through_appliance(events, context):
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    ec2 = boto3.client('ec2', config=config)

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
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    ec2 = boto3.client('ec2', config=config)
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


def _get_nat_routes_filter(nat_gw_id: str,
                           private_subnet_id: str = None,
                           destination_ipv4_cidr_block: str = None) -> List[str]:
    filters = [{'Name': 'route.nat-gateway-id', 'Values': [nat_gw_id]}]
    if private_subnet_id:
        filters.append({'Name': 'association.subnet-id', 'Values': [private_subnet_id]})
    if destination_ipv4_cidr_block:
        filters.append({'Name': 'route.destination-cidr-block', 'Values': [destination_ipv4_cidr_block]})

    return filters


def _get_ipv4_routes_to_nat(boto3_ec2_client,
                            nat_gw_id: str,
                            private_subnet_id: str = None,
                            destination_ipv4_cidr_block=None) -> dict:
    describe_route_filters = _get_nat_routes_filter(nat_gw_id=nat_gw_id,
                                                    private_subnet_id=private_subnet_id,
                                                    destination_ipv4_cidr_block=destination_ipv4_cidr_block)
    print(f'filter: {describe_route_filters}')

    route_tables_response = boto3_ec2_client.describe_route_tables(Filters=describe_route_filters)
    if not route_tables_response['ResponseMetadata']['HTTPStatusCode'] == 200:
        print(route_tables_response)
        raise ValueError('Failed to get route tables')

    return [{'RouteTableId': rt['RouteTableId'],
             'Routes':[{'DestinationCidrBlock': route['DestinationCidrBlock']}
            for route in filter(lambda x: x.get('NatGatewayId', '') == nat_gw_id, rt['Routes'])]}
            for rt in route_tables_response['RouteTables']]


def _delete_route(boto3_ec2_client, route_table_id: str, destination_ipv4_cidr_block: str) -> dict:
    delete_route_response = boto3_ec2_client.delete_route(RouteTableId=route_table_id,
                                                          DestinationCidrBlock=destination_ipv4_cidr_block)
    if not delete_route_response['ResponseMetadata']['HTTPStatusCode'] == 200:
        print(delete_route_response)
        raise ValueError('Failed to delete route')


def _create_route(boto3_ec2_client, route_table_id: str,
                  destination_ipv4_cidr_block: str,
                  nat_gw_id: str) -> dict:
    create_route_response = boto3_ec2_client.create_route(RouteTableId=route_table_id,
                                                          DestinationCidrBlock=destination_ipv4_cidr_block,
                                                          NatGatewayId=nat_gw_id)
    if not create_route_response['ResponseMetadata']['HTTPStatusCode'] == 200:
        print(create_route_response)
        raise ValueError('Failed to delete route')

    return create_route_response


def _create_route_and_wait(boto3_ec2_client, route_table_id: str,
                           destination_ipv4_cidr_block: str,
                           nat_gw_id: str,
                           wait_timeout_seconds: int = 30) -> dict:

    route = _create_route(boto3_ec2_client=boto3_ec2_client,
                          route_table_id=route_table_id,
                          destination_ipv4_cidr_block=destination_ipv4_cidr_block,
                          nat_gw_id=nat_gw_id)

    start = time.time()
    elapsed = 0
    while elapsed <= wait_timeout_seconds:
        ipv4_rt_nat = _get_ipv4_routes_to_nat(boto3_ec2_client=boto3_ec2_client,
                                              nat_gw_id=nat_gw_id,
                                              private_subnet_id=None,
                                              destination_ipv4_cidr_block=destination_ipv4_cidr_block)
        if ipv4_rt_nat:
            return route

        end = time.time()
        logging.debug(f'time elapsed {elapsed} seconds. The last result:{ipv4_rt_nat}')
        time.sleep(10)
        elapsed = end - start

    raise TimeoutError(f'After {elapsed} route [{route}] hasn\'t been found in route table [{route_table_id}].')


def _check_if_route_already_exists(route_table_id: str, cidr_ipv4: str, current_routes: dict) -> bool:
    """
    Checks whether or not route already exist
    :param route_table_id: The ID of the route table
    :param cidr_ipv4: The IPv4 CIDR
    :param current_routes: The current routes
    """
    existing_rts = [rt for rt in current_routes
                    if rt.get('RouteTableId', '') == route_table_id]
    if existing_rts:
        routes = existing_rts[0].get('Routes', [])
        existing_routes = [r for r in routes
                           if r.get('DestinationCidrBlock', '') == cidr_ipv4]
        if existing_routes:
            return True

    return False


def get_nat_gw_routes(events, context):
    print('Creating ec2 client')
    print(events)
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    ec2 = boto3.client('ec2', config=config)

    if 'NatGatewayId' not in events:
        raise KeyError('Requires NatGatewayId')

    nat_gw_id = events['NatGatewayId']
    private_subnet_id = events['PrivateSubnetId'] if 'PrivateSubnetId' in events else None
    ipv4_rt_nat = _get_ipv4_routes_to_nat(boto3_ec2_client=ec2,
                                          nat_gw_id=nat_gw_id,
                                          private_subnet_id=private_subnet_id)

    if not ipv4_rt_nat:
        raise ValueError(f'Route tables and routes not found: nat={nat_gw_id}, subnet={private_subnet_id}')

    return {
        'Response': json.dumps(ipv4_rt_nat)
    }


def delete_nat_gw_routes(events, context):
    print('Creating ec2 client')
    print(events)
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    ec2 = boto3.client('ec2', config=config)

    if 'NatGatewayId' not in events:
        raise KeyError('Requires NatGatewayId')
    if 'OriginalValue' not in events:
        raise KeyError('Requires OriginalValue')

    nat_gw_id = events['NatGatewayId']
    private_subnet_id = events['PrivateSubnetId'] if 'PrivateSubnetId' in events else None
    original_value = json.loads(events['OriginalValue'])
    for route_table in original_value:
        route_table_id = route_table['RouteTableId']
        for route in route_table['Routes']:
            cidr = route['DestinationCidrBlock']
            _delete_route(boto3_ec2_client=ec2,
                          route_table_id=route_table_id,
                          destination_ipv4_cidr_block=cidr)

    ipv4_rt_nat = _get_ipv4_routes_to_nat(boto3_ec2_client=ec2,
                                          nat_gw_id=nat_gw_id,
                                          private_subnet_id=private_subnet_id)

    return {
        'Response': json.dumps(ipv4_rt_nat)
    }


def create_nat_gw_routes(events, context):
    print('Creating ec2 client')
    print(events)
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    ec2 = boto3.client('ec2', config=config)

    if 'NatGatewayId' not in events:
        raise KeyError('Requires NatGatewayId')
    if 'OriginalValue' not in events:
        raise KeyError('Requires OriginalValue')

    nat_gw_id = events['NatGatewayId']
    private_subnet_id = events['PrivateSubnetId'] if 'PrivateSubnetId' in events else None
    original_value = json.loads(events['OriginalValue'])

    ipv4_rt_nat = _get_ipv4_routes_to_nat(boto3_ec2_client=ec2,
                                          nat_gw_id=nat_gw_id,
                                          private_subnet_id=private_subnet_id)
    for route_table in original_value:
        route_table_id = route_table['RouteTableId']
        for route in route_table['Routes']:
            cidr = route['DestinationCidrBlock']
            exists = _check_if_route_already_exists(route_table_id=route_table_id,
                                                    cidr_ipv4=cidr,
                                                    current_routes=ipv4_rt_nat)
            if exists:
                print(f'The route to {cidr} already exists. Route tables is {route_table_id}')
                continue
            _create_route_and_wait(boto3_ec2_client=ec2,
                                   route_table_id=route_table_id,
                                   destination_ipv4_cidr_block=cidr,
                                   nat_gw_id=nat_gw_id)

    ipv4_rt_nat = _get_ipv4_routes_to_nat(boto3_ec2_client=ec2,
                                          nat_gw_id=nat_gw_id,
                                          private_subnet_id=private_subnet_id)

    return {
        'Response': json.dumps(ipv4_rt_nat)
    }
