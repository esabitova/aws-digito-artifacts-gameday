import pytest
import logging
import re
from pytest_bdd import (
    when,
    parsers,
    given
)
from sttable import parse_str_table
from resource_manager.src.resource_manager import ResourceManager
from resource_manager.src.ssm_document import SsmDocument


def pytest_addoption(parser):
    """
    Hook: https://docs.pytest.org/en/stable/reference.html#initialization-hooks
    :param parser: To add command line options
    """
    parser.addoption("--run_integration_tests",
                     action="store_true",
                     default=False,
                     help="Flag to execute integration tests.")
    parser.addoption("--keep_test_resources",
                     action="store_true",
                     default=False,
                     help="Flag to keep test resources (created by Resource Manager) after all tests. Default False.")
    parser.addoption("--pool_size",
                     action="store",
                     help="Comma separated key=value pair of cloud formation file template names mapped to number of pool size (Example: template_1=3, template_2=4)")

def pytest_sessionstart(session):
    '''
    Hook https://docs.pytest.org/en/stable/reference.html#initialization-hooks \n
    For this case we want to create test DDB tables before running any test.
    :param session: Tests session
    '''
    # Execute only when running integration tests
    if session.config.option.run_integration_tests:
        ResourceManager.init_ddb_tables()
        ResourceManager.fix_stalled_resources()


def pytest_sessionfinish(session, exitstatus):
    '''
    Hook https://docs.pytest.org/en/stable/reference.html#initialization-hooks \n
    :param session: The pytest session object.
    :param exitstatus (int): The status which pytest will return to the system.
    :return:
    '''

    # Execute only when running integration tests
    if session.config.option.run_integration_tests:
        if session.config.option.keep_test_resources:
            # In case if test execution was canceled/failed we want to make resources available for next execution.
            ResourceManager.fix_stalled_resources()
        else:
            logging.info("Destroying all test resources (use '--keep_test_resources' to keep resources for next execution)")
            ResourceManager.destroy_all_resources()


@pytest.fixture(scope='function', autouse=True)
def resource_manager(request):
    '''
    Creates ResourceManager fixture for every test case.
    :param request: The pytest request object
    :return: The resource manager fixture
    '''
    rm = ResourceManager()
    yield rm
    # Release resources after test execution is completed
    rm.release_resources()


@pytest.fixture(scope='function')
def ssm_document():
    '''
    Creates SsmDocument fixture to for every test case.
    :return:
    '''
    return SsmDocument()

@pytest.fixture(scope='function')
def ssm_test_cache():
    '''
    Cache for test. There may be cases when state between test steps can be changed,
    but we want to remember it to be able to verify how state was changed after.
    Example you can find in: .../documents/rds/test/force_aurora_failover/Tests/features/aurora_failover_cluster.feature
    '''
    cache = dict()
    return cache

@given(parsers.parse('the CloudFormation template "{cf_template_name}" as test resources\n{cf_input_parameters}'))
def set_up_cf_template(cf_template_name, cf_input_parameters, resource_manager):
    """
    Common step to specify cloud formation template with parameters for specific test. It can be reused with no
    need to define this step implementation for every test. However it should be mentioned in your feature file.
    Example you can find in: .../documents/rds/test/force_aurora_failover/Tests/features/aurora_failover_cluster.feature
    :param cf_template_name: The cloud formation template file name.
    :param cf_input_parameters: The table of parameters as input for cloud formation template
    :param resource_manager: The resource manager which will take care of managing given template deployment and providing reosurces for tests
    """
    cf_input_params = parse_str_table(cf_input_parameters).rows[0]
    resource_manager.add_cf_template(cf_template_name, **cf_input_params)

@given(parsers.parse('SSM automation document "{ssm_document_name}" executed\n{ssm_input_parameters}'), target_fixture='ssm_execution_id')
def execute_ssm_automation(ssm_document, ssm_document_name, resource_manager, ssm_test_cache, ssm_input_parameters):
    """
    Common step to execute SSM document. This step can be reused by multiple scenarios.
    :param ssm_document The SSM document object for SSM manipulation (mainly execution)
    :param ssm_document_name The SSM document name
    :param resource_manager The resource manager object to manipulate with testing resources
    :param ssm_test_cache The custom test cache
    :param ssm_input_parameters The SSM execution input parameters
    """
    cfn_output = resource_manager.get_cf_output_params()
    parameters = ssm_document.parse_input_parameters(cfn_output, ssm_test_cache, ssm_input_parameters)
    return ssm_document.execute(ssm_document_name, parameters)

@when(parsers.parse('SSM automation document "{ssm_document_name}" execution in status "{expected_status}"'))
def verify_ssm_automation_execution_in_status(ssm_document_name, expected_status, ssm_document, ssm_execution_id):
    """
    Common step to wait for SSM document execution completion status. This step can be reused by multiple scenarios.
    :param ssm_document_name The SSM document name
    :param expected_status The expected SSM document execution status
    :param ssm_document The SSM document object for SSM manipulation (mainly execution)
    :param ssm_execution_id The SSM document execution id to track
    """
    actual_status = ssm_document.wait_for_execution_completion(ssm_execution_id, ssm_document_name)
    assert expected_status == actual_status