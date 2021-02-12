import pytest
import logging
import boto3
from pytest_bdd import (
    when,
    parsers,
    given
)
from sttable import parse_str_table
from resource_manager.src.resource_manager import ResourceManager
from resource_manager.src.ssm_document import SsmDocument
from resource_manager.src.s3 import S3
from resource_manager.src.util.param_utils import parse_param_value, parse_param_values_from_table
from resource_manager.src.cloud_formation import CloudFormationTemplate


def pytest_addoption(parser):
    """
    Hook: https://docs.pytest.org/en/stable/reference.html#initialization-hooks
    :param parser: To add command line options
    """
    parser.addoption("--run_integration_tests",
                     action="store_true",
                     default=False,
                     help="Flag to execute integration tests.")
    parser.addoption("--aws_profile",
                     action="store",
                     default='default',
                     help="Boto3 session profile name")
    parser.addoption("--keep_test_resources",
                     action="store_true",
                     default=False,
                     help="Flag to keep test resources (created by Resource Manager) after all tests. Default False.")
    parser.addoption("--pool_size",
                     action="store",
                     help="Comma separated key=value pair of cloud formation file template names mapped to number of "
                          "pool size (Example: template_1=3, template_2=4)")


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    # In case if running integration tests we don't report coverage
    if config.option.run_integration_tests:
        cov_plugin = config.pluginmanager.get_plugin("_cov")
        if cov_plugin:
            cov_plugin.options.no_cov = True


def pytest_sessionstart(session):
    '''
    Hook https://docs.pytest.org/en/stable/reference.html#initialization-hooks \n
    For this case we want to create test DDB tables before running any test.
    :param session: Tests session
    '''
    # Execute when running integration tests
    if session.config.option.run_integration_tests:
        boto3_session = get_boto3_session(session.config.option.aws_profile)
        cfn_helper = CloudFormationTemplate(boto3_session)
        s3_helper = S3(boto3_session)
        rm = ResourceManager(cfn_helper, s3_helper)
        rm.init_ddb_tables(boto3_session)
        rm.fix_stalled_resources()


def pytest_sessionfinish(session, exitstatus):
    '''
    Hook https://docs.pytest.org/en/stable/reference.html#initialization-hooks \n
    :param session: The pytest session object.
    :param exitstatus (int): The status which pytest will return to the system.
    :return:
    '''
    # Execute only when running integration tests
    if session.config.option.run_integration_tests:
        boto3_session = get_boto3_session(session.config.option.aws_profile)
        cfn_helper = CloudFormationTemplate(boto3_session)
        s3_helper = S3(boto3_session)
        rm = ResourceManager(cfn_helper, s3_helper)
        if session.config.option.keep_test_resources:
            # In case if test execution was canceled/failed we want to make resources available for next execution.
            rm.fix_stalled_resources()
        else:
            logging.info(
                "Destroying all test resources (use '--keep_test_resources' to keep resources for next execution)")
            rm.destroy_all_resources()


@pytest.fixture(scope='session')
def boto3_session(request):
    '''
    Creates session for given profile name. More about how to configure AWS profile:
    https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-profiles.html
    :param request The pytest request object
    '''
    return get_boto3_session(request.config.option.aws_profile)


@pytest.fixture(scope='function')
def resource_manager(request, boto3_session):
    '''
    Creates ResourceManager fixture for every test case.
    :param request: The pytest request object
    :return: The resource manager fixture
    '''
    cfn_helper = CloudFormationTemplate(boto3_session)
    s3_helper = S3(boto3_session)
    rm = ResourceManager(cfn_helper, s3_helper)
    yield rm
    # Release resources after test execution is completed
    rm.release_resources()


@pytest.fixture(scope='function')
def ssm_document(boto3_session):
    '''
    Creates SsmDocument fixture to for every test case.
    :return:
    '''
    return SsmDocument(boto3_session)


@pytest.fixture(scope='function')
def ssm_test_cache():
    '''
    Cache for test. There may be cases when state between test steps can be changed,
    but we want to remember it to be able to verify how state was changed after.
    Example you can find in: .../documents/rds/test/force_aurora_failover/Tests/features/aurora_failover_cluster.feature
    '''
    cache = dict()
    return cache

@pytest.fixture(scope='function')
def cfn_output_params(resource_manager):

    return resource_manager.get_cfn_output_params()


def get_boto3_session(aws_profile):
    '''
    Helper to create boto3 session based on given AWS profile.
    :param The AWS profile name.
    '''
    logging.info("Creating boto3 session for [{}] profile.".format(aws_profile))
    return boto3.Session(profile_name=aws_profile)


@given(parsers.parse('the cloud formation templates as integration test resources\n{cfn_input_parameters}'))
def set_up_cfn_template_resources(resource_manager, cfn_input_parameters, ssm_test_cache):
    """
    Common step to specify cloud formation template with parameters for specific test. It can be reused with no
    need to define this step implementation for every test. However it should be mentioned in your feature file.
    Example you can find in: .../documents/rds/test/force_aurora_failover/Tests/features/aurora_failover_cluster.feature
    :param resource_manager: The resource manager which will take care of managing given template deployment
    and providing resources for tests
    :param cfn_input_parameters: The table of parameters as input for cloud formation template
    """
    for cfn_params_row in parse_str_table(cfn_input_parameters).rows:
        if cfn_params_row.get('CfnTemplatePath') is None or len(cfn_params_row.get('CfnTemplatePath')) < 1 \
                or cfn_params_row.get('ResourceType') is None or len(cfn_params_row.get('ResourceType')) < 1:
            raise Exception('Required parameters [CfnTemplatePath] and [ResourceType] should be presented.')
        cf_template_path = cfn_params_row.pop('CfnTemplatePath')
        resource_type = cfn_params_row.pop('ResourceType')
        cf_input_params = {}
        for param, param_val_ref in cfn_params_row.items():
            if len(param_val_ref) > 0:
                value = parse_param_value(param_val_ref, {'cache': ssm_test_cache})
                cf_input_params[param] = str(value)
        rm_resource_type = ResourceManager.ResourceType.from_string(resource_type)
        resource_manager.add_cfn_template(cf_template_path, rm_resource_type, **cf_input_params)


@when(parsers.parse('SSM automation document "{ssm_document_name}" executed\n{ssm_input_parameters}'))
@given(parsers.parse('SSM automation document "{ssm_document_name}" executed\n{ssm_input_parameters}'))
def execute_ssm_automation(ssm_document, ssm_document_name, resource_manager, ssm_test_cache, ssm_input_parameters):
    """
    Common step to execute SSM document. This step can be reused by multiple scenarios.
    :param ssm_document The SSM document object for SSM manipulation (mainly execution)
    :param ssm_document_name The SSM document name
    :param resource_manager The resource manager object to manipulate with testing resources
    :param ssm_test_cache The custom test cache
    :param ssm_input_parameters The SSM execution input parameters
    """
    cfn_output = resource_manager.get_cfn_output_params()
    parameters = ssm_document.parse_input_parameters(cfn_output, ssm_test_cache, ssm_input_parameters)
    execution_id = ssm_document.execute(ssm_document_name, parameters)

    # Caching automation execution ids to be able to use them in test as parameter references in data tables
    # |ExecutionId               | <- parameters name can be anything
    # |{{cache:SsmExecutionId>1}}| <- cache execution id reference. Number '1' refers to sequence of executions in test.
    exec_cache_key = 'SsmExecutionId'
    cached_execution = ssm_test_cache.get(exec_cache_key)
    if cached_execution is None:
        ssm_test_cache[exec_cache_key] = {'1': execution_id}
    else:
        sequence_number = str(len(cached_execution) + 1)
        cached_execution[sequence_number] = execution_id
        ssm_test_cache[exec_cache_key] = cached_execution
    return execution_id


@when(parsers.parse('SSM automation document "{ssm_document_name}" execution in status "{expected_status}"\n{parameters}'))
def wait_for_execution_completion(ssm_document_name, expected_status, ssm_document, ssm_test_cache, parameters):
    """
    Common step to wait for SSM document execution completion status. This step can be reused by multiple scenarios.
    :param ssm_document_name The SSM document name
    :param expected_status The expected SSM document execution status
    :param ssm_document The SSM document object for SSM manipulation (mainly execution)
    :param ssm_test_cache The custom test cache
    :param parameters The input parameters
    """
    cfn_output = resource_manager.get_cfn_output_params()
    parameters = parse_param_values_from_table(parameters, {'cache': ssm_test_cache, 'cfn-output': cfn_output})
    if len(parameters) < 1 or parameters[0].get['ExecutionId'] is None:
        raise Exception('Parameter with name [ExecutionId] should be provided')
    actual_status = ssm_document.wait_for_execution_completion(parameters[0].get['ExecutionId'], ssm_document_name)
    assert expected_status == actual_status


@when(parsers.parse('SSM automation document "{ssm_document_name}" execution in status "{expected_status}"\n{input_parameters}'))
def wait_for_execution_completion_with_params(resource_manager, ssm_document_name, expected_status,
                                              ssm_document, input_parameters, ssm_test_cache):
    """
    Common step to wait for SSM document execution completion status. This step can be reused by multiple scenarios.
    :param resource_manager The resource manager object to manipulate with testing resources
    :param ssm_document_name The SSM document name
    :param input_parameters The input parameters
    :param expected_status The expected SSM document execution status
    :param ssm_document The SSM document object for SSM manipulation (mainly execution)
    :param ssm_test_cache The custom test cache
    """
    cfn_output = resource_manager.get_cfn_output_params()
    parameters = parse_param_values_from_table(input_parameters, {'cache': ssm_test_cache, 'cfn-output': cfn_output})
    ssm_execution_id = parameters[0].get('ExecutionId')
    if ssm_execution_id is None:
        raise Exception('Parameter with name [ExecutionId] should be provided')
    actual_status = ssm_document.wait_for_execution_completion(ssm_execution_id, ssm_document_name)
    assert expected_status == actual_status


