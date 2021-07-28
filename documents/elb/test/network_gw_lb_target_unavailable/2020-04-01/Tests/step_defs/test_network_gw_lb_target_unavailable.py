
from pytest_bdd import scenario, given, parsers, when, then

from resource_manager.src.util.boto3_client_factory import client
from resource_manager.src.util.common_test_utils import extract_param_value, put_to_ssm_test_cache


# @scenario('../features/network_gw_lb_target_unavailable_usual_case.feature',
#           'Create Network LB and execute automation to make the target group unavailable')
# def test_network_lb_target_unavailable_usual_case():
#     """Create Network LB and execute automation to make the target group unavailable"""
#
#
# @scenario('../features/network_gw_lb_target_unavailable_usual_case.feature',
#           'Create Network LB and execute automation to make the target group unavailable '
#           'with target groups specified')
# def test_network_lb_target_unavailable_usual_case_tg_specified():
#     """Create Network LB and execute automation to make the target group unavailable  with target groups specified"""
#
#
# @scenario('../features/network_gw_lb_target_unavailable_usual_case.feature',
#           'Create Gateway LB and execute automation to make the target group unavailable')
# def test_gateway_target_unavailable_usual_case():
#     """Create Gateway LB and execute automation to make the target group unavailable"""
#
#
# @scenario('../features/network_gw_lb_target_unavailable_usual_case.feature',
#           'Create Gateway LB and execute automation to make the target group unavailable'
#           ' with target groups specified')
# def test_gateway_target_unavailable_usual_case_tg_specified():
#     """Create Gateway LB and execute automation to make the target group unavailable"""


@scenario('../features/network_gw_lb_target_unavailable_rollback_previous.feature',
          'Create Network LB and execute automation to make the target group unavailable in rollback')
def test_network_lb_target_unavailable_rollback_previous():
    """Create Network LB and execute automation to make the target group unavailable in rollback"""


@scenario('../features/network_gw_lb_target_unavailable_rollback_previous.feature',
          'Create Gateway LB and execute automation to make the target group unavailable in rollback')
def test_gateway_lb_target_unavailable_rollback_previous():
    """Create Gateway LB and execute automation to make the target group unavailable in rollback"""


# @scenario('../features/network_gw_lb_target_unavailable_failed.feature',
#           'Create Network LB and execute automation to make the target group unavailable to test failure case')
# def test_network_lb_target_unavailable_failed():
#     """Create Network LB and execute automation to make the target group unavailable to test failure case"""
#
#
# @scenario('../features/network_gw_lb_target_unavailable_failed.feature',
#           'Create Gateway LB and execute automation to make the target group unavailable to test failure case')
# def test_gateway_lb_target_unavailable_failed():
#     """Create Gateway LB and execute automation to make the target group unavailable to test failure case"""


cache_target_group_health_port_expression = 'cache target group HealthCheckPort as "{cache_property}" "{cache_key}" ' \
                                            'SSM automation execution\n{input_parameters}'


@given(parsers.parse(cache_target_group_health_port_expression))
@when(parsers.parse(cache_target_group_health_port_expression))
@then(parsers.parse(cache_target_group_health_port_expression))
def cache_target_group_health_port(boto3_session, ssm_test_cache, resource_pool,
                                   cache_property, cache_key, input_parameters):
    elb_client = client('elbv2', boto3_session)
    lb_arn = extract_param_value(input_parameters, 'LoadBalancerArn', resource_pool, ssm_test_cache)
    target_groups = elb_client.describe_target_groups(LoadBalancerArn=lb_arn)
    try:
        port = target_groups['TargetGroups'][0]['HealthCheckPort']
        put_to_ssm_test_cache(ssm_test_cache, cache_key, cache_property, port)
    except KeyError:
        raise AssertionError(f'There are no Target Groups with HealthCheck ports set in lb: {lb_arn}')
