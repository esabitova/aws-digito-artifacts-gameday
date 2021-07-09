from pytest_bdd import given, parsers, when
from resource_manager.src.util.elb_utils import (
    send_incorrect_requests)
from resource_manager.src.util.common_test_utils import (extract_param_value)

CIPHERS = (
    'AES128-GCM-SHA256:ECDHE-RSA-AES128-SHA256:AES256-SHA'
)


@given(parsers.parse('send incorrect https requests {number} times\n{input_parameters}'))
@when(parsers.parse('send incorrect https requests {number} times\n{input_parameters}'))
def send_incorrect_https_requests(boto3_session, resource_pool, ssm_test_cache, number, input_parameters):
    url: str = extract_param_value(input_parameters, "TestUrl", resource_pool, ssm_test_cache)
    url = f'https://{url}'
    send_incorrect_requests(boto3_session, url, int(number))
