from pytest_bdd import scenario, given, parsers, when, then

from resource_manager.src.util.boto3_client_factory import client
from resource_manager.src.util.common_test_utils import extract_param_value, put_to_ssm_test_cache


@scenario('../features/application_lb_network_unavailable_usual_case.feature',
          'Execute SSM automation document Digito-ApplicationLbNetworkUnavailable_2020-04-01 usual case')
def test_application_lb_network_unavailable_usual_case():
    pass


@scenario('../features/application_lb_network_unavailable_usual_case.feature',
          'Execute SSM automation document Digito-ApplicationLbNetworkUnavailable_2020-04-01 with '
          'SecurityGroupIdsToDelete param specified')
def test_application_lb_network_unavailable_sg_ids_specified():
    pass


@scenario('../features/application_lb_network_unavailable_rollback_previous.feature',
          'Execute SSM automation document Digito-ApplicationLbNetworkUnavailable_2020-04-01 in rollback')
def test_application_lb_network_unavailable_automation_rollback():
    pass


@scenario('../features/application_lb_network_unavailable_failed.feature',
          'Execute SSM automation document Digito-ApplicationLbNetworkUnavailable_2020-04-01 to test failure case')
def test_application_lb_network_unavailable_failure_case():
    pass


@scenario('../features/application_lb_network_unavailable_failed.feature',
          'Execute SSM automation document Digito-ApplicationLbNetworkUnavailable_2020-04-01 '
          'with SecurityGroupIdsToDelete param specified to test failure case')
def test_application_lb_network_unavailable_with_param_specified_failure_case():
    pass


@given(parsers.parse('cache load balancer security groups as "{cache_property}" "{cache_key}" '
                     'SSM automation execution\n{input_parameters}'))
@when(parsers.parse('cache load balancer security groups as "{cache_property}" "{cache_key}" '
                    'SSM automation execution\n{input_parameters}'))
@then(parsers.parse('cache load balancer security groups as "{cache_property}" "{cache_key}" '
                    'SSM automation execution\n{input_parameters}'))
def cache_lb_security_groups(boto3_session, ssm_test_cache, resource_pool,
                             cache_property, cache_key, input_parameters):
    elb_client = client('elbv2', boto3_session)
    lb_arn = extract_param_value(input_parameters, 'LoadBalancerArn', resource_pool, ssm_test_cache)
    response = elb_client.describe_load_balancers(LoadBalancerArns=[lb_arn])

    try:
        groups = response['LoadBalancers'][0]['SecurityGroups']
        groups.sort()
        groups_str = ','.join(groups)
        put_to_ssm_test_cache(ssm_test_cache, cache_key, cache_property, groups_str)
    except KeyError:
        raise AssertionError(f'SecurityGroups not found in LoadBalancer: {lb_arn}')
