import pytest
import logging
import boto3
import time
from pytest_bdd import (
    when,
    parsers,
    given,
    then
)
from sttable import parse_str_table
from datetime import timedelta, datetime
from resource_manager.src.resource_manager import ResourceManager
from resource_manager.src.ssm_document import SsmDocument
from resource_manager.src.s3 import S3
from resource_manager.src.util.cw_util import get_ec2_metric_max_datapoint
from resource_manager.src.util.param_utils import parse_param_value, parse_param_values_from_table
from resource_manager.src.cloud_formation import CloudFormationTemplate
from resource_manager.src.util.ssm_utils import get_ssm_step_interval, get_ssm_step_status
from pytest import ExitCode
from botocore.exceptions import ClientError
from publisher.publish_documents import PublishDocuments


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
    :param exitstatus(int): The status which pytest will return to the system.
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
    # Applicable only for integration tests
    if request.session.config.option.run_integration_tests:
        return get_boto3_session(request.config.option.aws_profile)
    return boto3.Session()


@pytest.fixture(scope='function')
def cfn_output_params(resource_manager):
    """
    Fixture for cfn_output_params from resource manager.
    :param resource_manager The resource manager
    """
    return resource_manager.get_cfn_output_params()

@pytest.fixture(scope='function')
def resource_manager(request, boto3_session):
    '''
    Creates ResourceManager fixture for every test case.
    :param request: The pytest request object
    :param boto3_session The boto3 session
    :return: The resource manager fixture
    '''
    cfn_helper = CloudFormationTemplate(boto3_session)
    s3_helper = S3(boto3_session)
    rm = ResourceManager(cfn_helper, s3_helper)
    yield rm
    # Release resources after test execution is completed if test was not manually
    # interrupted/cancelled. In case of interruption resources will be
    # released and fixed on 'pytest_sessionfinish'
    if request.session.exitstatus != ExitCode.INTERRUPTED:
        rm.release_resources()


@pytest.fixture(scope='function')
def ssm_document(boto3_session):
    '''
    Creates SsmDocument fixture to for every test case.
    :return:
    '''
    return SsmDocument(boto3_session)


@pytest.fixture(autouse=True, scope='function')
def setup(request, ssm_test_cache, boto3_session):
    """
    Terminates SSM execution after each test execution. In case if test failed and test didn't perform any
    SSM execution termination step we don't want to leave SSM running after test failure.
    :param request The pytest request object
    :param ssm_test_cache The test cache
    :param boto3_session The boto3 session
    """
    def tear_down():
        # Terminating SSM automation execution at the end of each test.
        ssm = boto3_session.client('ssm')
        cached_executions = ssm_test_cache.get('SsmExecutionId')
        if cached_executions is not None:
            for index, exec_id in cached_executions.items():
                execution_url = 'https://{}.console.aws.amazon.com/systems-manager/automation/execution/{}' \
                    .format(boto3_session.region_name, exec_id)
                try:
                    logging.info("Canceling SSM execution: {}".format(execution_url))
                    ssm.stop_automation_execution(AutomationExecutionId=exec_id, Type='Cancel')
                except ClientError as e:
                    logging.error("Failed to cancel SSM execution [%s] due to: %s", execution_url, e.response)

    # Applicable only for integration tests
    if request.session.config.option.run_integration_tests:
        request.addfinalizer(tear_down)


@pytest.fixture(scope='function')
def ssm_test_cache():
    '''
    Cache for test. There may be cases when state between test steps can be changed,
    but we want to remember it to be able to verify how state was changed after.
    Example you can find in: .../documents/rds/test/force_aurora_failover/Tests/features/aurora_failover_cluster.feature
    '''
    cache = dict()
    return cache


def get_boto3_session(aws_profile):
    '''
    Helper to create boto3 session based on given AWS profile.
    :param The AWS profile name.
    '''
    logging.info("Creating boto3 session for [{}] profile.".format(aws_profile))
    return boto3.Session(profile_name=aws_profile)


@given(parsers.parse('published "{ssm_document_name}" SSM document'))
def publish_ssm_document(boto3_session, ssm_document_name):
    """
    Publish SSM document using 'publisher.publish_documents.PublishDocuments'.
    :param boto3_session The boto3 session
    :param ssm_document_name The SSM document name
    """
    p = PublishDocuments(boto3_session)
    documents_metadata = p.get_documents_list_by_names([ssm_document_name])
    p.publish_document(documents_metadata)


@given(parsers.parse('the cloud formation templates as integration test resources\n{cfn_input_parameters}'))
def set_up_cfn_template_resources(resource_manager, cfn_input_parameters, ssm_test_cache):
    """
    Common step to specify cloud formation template with parameters for specific test. It can be reused with no
    need to define this step implementation for every test. However it should be mentioned in your feature file.
    Example you can find in: .../documents/rds/test/force_aurora_failover/Tests/features/aurora_failover_cluster.feature
    :param resource_manager: The resource manager which will take care of managing given template deployment
    and providing resources for tests
    :param cfn_input_parameters: The table of parameters as input for cloud formation template
    :param ssm_test_cache The custom test cache
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
def execute_ssm_automation(ssm_document, ssm_document_name, cfn_output_params, ssm_test_cache, ssm_input_parameters):
    """
    Common step to execute SSM document. This step can be reused by multiple scenarios.
    :param ssm_document The SSM document object for SSM manipulation (mainly execution)
    :param ssm_document_name The SSM document name
    :param cfn_output_params The resource manager object to manipulate with testing resources
    :param ssm_test_cache The custom test cache
    :param ssm_input_parameters The SSM execution input parameters
    """
    parameters = ssm_document.parse_input_parameters(cfn_output_params, ssm_test_cache, ssm_input_parameters)
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


@given(parsers.parse('SSM automation document "{ssm_document_name}" execution in status "{expected_status}"\n{input_parameters}'))
@when(parsers.parse('SSM automation document "{ssm_document_name}" execution in status "{expected_status}"\n{input_parameters}'))
@then(parsers.parse('SSM automation document "{ssm_document_name}" execution in status "{expected_status}"\n{input_parameters}'))
def wait_for_execution_completion_with_params(cfn_output_params, ssm_document_name, expected_status,
                                              ssm_document, input_parameters, ssm_test_cache):
    """
    Common step to wait for SSM document execution completion status. This step can be reused by multiple scenarios.
    :param cfn_output_params The cfn output params from resource manager
    :param ssm_document_name The SSM document name
    :param input_parameters The input parameters
    :param expected_status The expected SSM document execution status
    :param ssm_document The SSM document object for SSM manipulation (mainly execution)
    :param ssm_test_cache The custom test cache
    """
    parameters = parse_param_values_from_table(input_parameters, {'cache': ssm_test_cache,
                                                                  'cfn-output': cfn_output_params})
    ssm_execution_id = parameters[0].get('ExecutionId')
    if ssm_execution_id is None:
        raise Exception('Parameter with name [ExecutionId] should be provided')
    actual_status = ssm_document.wait_for_execution_completion(ssm_execution_id, ssm_document_name)
    assert expected_status == actual_status


@when(parsers.parse('Wait for the SSM automation document "{ssm_document_name}" execution is on step "{ssm_step_name}" in status "{expected_status}" for "{time_to_wait}" seconds\n{input_parameters}'))
def wait_for_execution_step_with_params(cfn_output_params, ssm_document_name, ssm_step_name, time_to_wait,
                                        expected_status, ssm_document, input_parameters, ssm_test_cache):
    """
    Common step to wait for SSM document execution step waiting of final status
    :param cfn_output_params The cfn output params from resource manager
    :param ssm_document_name The SSM document name
    :param ssm_step_name The SSM document step name
    :param time_to_wait Timeout in seconds to wait until step status is resolved
    :param expected_status The expected SSM document execution status
    :param input_parameters The input parameters
    :param ssm_document The SSM document object for SSM manipulation (mainly execution)
    :param ssm_test_cache The custom test cache
    """
    parameters = parse_param_values_from_table(input_parameters, {'cache': ssm_test_cache,
                                                                  'cfn-output': cfn_output_params})
    ssm_execution_id = parameters[0].get('ExecutionId')
    if ssm_execution_id is None:
        raise Exception('Parameter with name [ExecutionId] should be provided')
    if expected_status == 'InProgress':
        actual_status = ssm_document.wait_for_execution_step_status_is_in_progress(
            ssm_execution_id, ssm_document_name, ssm_step_name, int(time_to_wait)
        )
    else:
        actual_status = ssm_document.wait_for_execution_step_status_is_terminal_or_waiting(
            ssm_execution_id, ssm_document_name, ssm_step_name, int(time_to_wait)
        )
    assert expected_status == actual_status


@given(parsers.parse('the cached input parameters\n{input_parameters}'))
def given_cached_input_parameters(ssm_test_cache, input_parameters):
    for parm_name, param_val in parse_str_table(input_parameters).rows[0].items():
        ssm_test_cache[parm_name] = str(param_val)


@then(parsers.parse('terminate "{ssm_document_name}" SSM automation document\n{input_parameters}'))
def terminate_ssm_execution(boto3_session, cfn_output_params, ssm_test_cache, ssm_document, input_parameters):
    ssm = boto3_session.client('ssm')
    parameters = ssm_document.parse_input_parameters(cfn_output_params, ssm_test_cache, input_parameters)
    ssm.stop_automation_execution(AutomationExecutionId=parameters['ExecutionId'][0], Type='Cancel')


@when(parsers.parse('SSM automation document "{ssm_document_name}" executed with rollback\n{ssm_input_parameters}'))
def execute_ssm_with_rollback(ssm_document_name, ssm_input_parameters, ssm_test_cache, cfn_output_params, ssm_document):
    parameters = ssm_document.parse_input_parameters(cfn_output_params, ssm_test_cache, ssm_input_parameters)
    execution_id = ssm_document.execute(ssm_document_name, parameters)
    ssm_test_cache['SsmRollbackExecutionId'] = execution_id
    return execution_id


@then(parsers.parse('sleep for "{seconds}" seconds'))
def sleep_secons(seconds):
    # Need to wait for more than 5 minutes for metric to be reported
    logging.info('Sleeping for [{}] seconds'.format(seconds))
    time.sleep(int(seconds))


@then(parsers.parse('assert SSM automation document step "{step_name}" execution in status "{expected_step_status}"\n{parameters}'))
def verify_step_in_status(boto3_session, step_name, expected_step_status, ssm_test_cache, parameters):
    params = parse_param_values_from_table(parameters, {'cache': ssm_test_cache})
    current_step_status = get_ssm_step_status(boto3_session, params[0]['ExecutionId'], step_name)
    assert expected_step_status == current_step_status


@when(parsers.parse('assert "{metric_name}" metric point "{operator}" than "{exp_perc}" percent(s)\n{input_params}'))
@then(parsers.parse('assert "{metric_name}" metric point "{operator}" than "{exp_perc}" percent(s)\n{input_params}'))
def assert_utilization(metric_name, operator, exp_perc, cfn_output_params, input_params, ssm_test_cache, boto3_session):
    """
    Asserts if particular metric reached desired point.
    :param exp_perc The expected metric  percentage point
    :param cfn_output_params The cfn output parameters from resource manager
    :param input_params The input parameters from step definition
    :param ssm_test_cache The test cache
    :param boto3_session The boto3 session
    :param metric_name The metric name to assert
    :param operator The operator to use for assertion
    """
    params = parse_param_values_from_table(input_params, {'cfn-output': cfn_output_params, 'cache': ssm_test_cache})
    input_param_row = params[0]
    exec_id = input_param_row.pop('ExecutionId')
    metric_namespace = input_param_row.pop('Namespace')
    step_name = input_param_row.pop('StepName')
    metric_period = int(input_param_row.pop('MetricPeriod'))

    exec_start, exec_end = get_ssm_step_interval(boto3_session, exec_id, step_name)
    # We need to include metric period to metric start time to have latest metrics
    exec_start = exec_start + timedelta(seconds=metric_period)
    act_perc = get_ec2_metric_max_datapoint(boto3_session, exec_start, datetime.utcnow(),
                                            metric_namespace, metric_name, input_param_row, metric_period)
    if operator == 'greaterOrEqual':
        assert int(act_perc) >= int(exp_perc)
    elif operator == 'greater':
        assert int(act_perc) > int(exp_perc)
    elif operator == 'lessOrEqual':
        assert int(act_perc) <= int(exp_perc)
    elif operator == 'less':
        assert int(act_perc) < int(exp_perc)
    else:
        raise Exception('Operator for [{}] is not supported'.format(operator))


@when(parsers.parse('Approve SSM automation document\n{input_parameters}'))
def approve_automation(cfn_output_params, ssm_test_cache, ssm_document, input_parameters):
    """
    Common step to approve waiting execution
    :param cfn_output_params The cfn output params from resource manager
    :param ssm_test_cache The custom test cache
    :param ssm_document The SSM document object for SSM manipulation (mainly execution)
    :param input_parameters The input parameters
    """
    parameters = parse_param_values_from_table(input_parameters, {'cache': ssm_test_cache,
                                                                  'cfn-output': cfn_output_params})
    ssm_execution_id = parameters[0].get('ExecutionId')
    if ssm_execution_id is None:
        raise Exception('Parameter with name [ExecutionId] should be provided')
    ssm_document.send_step_approval(ssm_execution_id)


@when(parsers.parse('Reject SSM automation document\n{input_parameters}'))
def reject_automation(cfn_output_params, ssm_test_cache, ssm_document, input_parameters):
    """
    Common step to reject waiting execution
    :param cfn_output_params The cfn output params from resource manager
    :param ssm_test_cache The custom test cache
    :param ssm_document The SSM document object for SSM manipulation (mainly execution)
    :param input_parameters The input parameters
    """
    parameters = parse_param_values_from_table(input_parameters, {'cache': ssm_test_cache,
                                                                  'cfn-output': cfn_output_params})
    ssm_execution_id = parameters[0].get('ExecutionId')
    if ssm_execution_id is None:
        raise Exception('Parameter with name [ExecutionId] should be provided')
    ssm_document.send_step_approval(ssm_execution_id, is_approved=False)
