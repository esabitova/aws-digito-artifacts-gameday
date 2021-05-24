import logging
import random
import re
import string
import time
import uuid
from datetime import datetime

import boto3
import pytest
from botocore.exceptions import ClientError
from pytest import ExitCode
from pytest_bdd import (
    when,
    given,
    then
)
from pytest_bdd.parsers import parse
from sttable import parse_str_table

from publisher.src.publish_documents import PublishDocuments
from resource_manager.src.alarm_manager import AlarmManager
from resource_manager.src.cloud_formation import CloudFormationTemplate
from resource_manager.src.resource_model import ResourceModel
from resource_manager.src.resource_pool import ResourcePool
from resource_manager.src.s3 import S3
from resource_manager.src.ssm_document import SsmDocument
from resource_manager.src.util.common_test_utils import put_to_ssm_test_cache
from resource_manager.src.util.cw_util import get_ec2_metric_max_datapoint, wait_for_metric_alarm_state
from resource_manager.src.util.cw_util import get_metric_alarm_state
from resource_manager.src.util.cw_util import wait_for_metric_data_point
from resource_manager.src.util.enums.alarm_state import AlarmState
from resource_manager.src.util.enums.operator import Operator
from resource_manager.src.util.param_utils import parse_param_value, parse_param_values_from_table
from resource_manager.src.util.param_utils import parse_pool_size
from resource_manager.src.util.ssm_utils import get_ssm_execution_output_value
from resource_manager.src.util.ssm_utils import get_ssm_step_interval, get_ssm_step_status
from resource_manager.src.util.ssm_utils import send_step_approval
from resource_manager.src.util.sts_utils import assume_role_session


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
                          "pool size (Example: template_1=3, template_2=4).")
    parser.addoption("--distributed_mode",
                     action="store_true",
                     default=False,
                     help="Flag to run integration tests in distributed mode "
                          "(multi session/machines targeting same AWS account). "
                          "NOTE: Flag should be used only for CI/CD pipeline, not for personal usage.")
    parser.addoption("--target_service",
                     action="store",
                     help="If specified, style validator would be run only against documents for this service. "
                          "The default behavior being that it would be run for all existing services")


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
        # Generating testing session id in order to tie test resources to specific session, so that when
        # running tests in parallel by multiple machines (sessions) tests will not try to change state of
        # resources which are still in use by other sessions.
        test_session_id = str(uuid.uuid4())
        session.config.option.test_session_id = test_session_id

        boto3_session = get_boto3_session(session.config.option.aws_profile)
        cfn_helper = CloudFormationTemplate(boto3_session)
        s3_helper = S3(boto3_session)
        rm = ResourcePool(cfn_helper, s3_helper, dict(), None)
        rm.init_ddb_tables(boto3_session)
        # Distributed mode is considered mode when we executing integration tests on multiple testing sessions/machines
        # and targeting same AWS account resources, in this case we should not perform resource fixing, since it
        # can change resources state which is in use by other session.
        if not session.config.option.distributed_mode:
            rm.fix_stalled_resources()


def pytest_sessionfinish(session, exitstatus):
    '''
    Hook https://docs.pytest.org/en/stable/reference.html#initialization-hooks \n
    :param session: The pytest session object.
    :param exitstatus(int): The status which pytest will return to the system.
    :return:
    '''
    # Execute only when running integration tests and disabled skip session level hooks
    # In case we do execute tests not in single session, for example in different machines, we don't want
    # to perform resource fix/destroy since one session can try to modify resource state which is used
    # by another session.At this moment this case is used on CodeCommit pipeline actions where we do
    # execute tests in parallel on different machines in same AWS account.

    if session.config.option.run_integration_tests:
        test_session_id = session.config.option.test_session_id
        boto3_session = get_boto3_session(session.config.option.aws_profile)
        cfn_helper = CloudFormationTemplate(boto3_session)
        s3_helper = S3(boto3_session)
        rm = ResourcePool(cfn_helper, s3_helper, dict(), test_session_id)
        if session.config.option.keep_test_resources:
            # In case if test execution was canceled/failed we want to make resources available for next execution.
            rm.fix_stalled_resources()
        else:
            logging.info(
                "Destroying all test resources (use '--keep_test_resources' to keep resources for next execution)")
            # NOTE: We don't want to call this when running tests on multiple machines (sessions). Since resources
            # may still be in use by other machines (sessions).
            rm.destroy_all_resources()


@pytest.fixture(scope='session')
def target_service(request):
    return request.config.option.target_service


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
def cfn_output_params(resource_pool):
    """
    Fixture for cfn_output_params from resource pool.
    :param resource_pool The resource pool
    """
    return resource_pool.get_cfn_output_params()


@pytest.fixture(scope='function')
def cfn_installed_alarms(alarm_manager):
    """
    Fixture for cfn_installed_alarms from alarm_manager manager.
    """
    return alarm_manager.get_deployed_alarms()


@pytest.fixture(scope='function')
def resource_pool(request, boto3_session):
    """
    Creates ResourcePool fixture for every test case.
    :param request: The pytest request object
    :param boto3_session The boto3 session
    :return: The resource pool fixture
    """
    test_session_id = request.session.config.option.test_session_id
    cfn_helper = CloudFormationTemplate(boto3_session)
    s3_helper = S3(boto3_session)
    custom_pool_size = parse_pool_size(request.session.config.option.pool_size)
    rp = ResourcePool(cfn_helper, s3_helper, custom_pool_size, test_session_id)
    yield rp
    # Release resources after test execution is completed if test was not manually
    # interrupted/cancelled. In case of interruption resources will be
    # released and fixed on 'pytest_sessionfinish'
    if request.session.exitstatus != ExitCode.INTERRUPTED:
        rp.release_resources()


@pytest.fixture(scope='function')
def ssm_document(boto3_session):
    """
    Creates SsmDocument fixture to for every test case.
    """
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


@pytest.fixture
def alarm_manager(boto3_session):
    """
    Container for alarms deployed during a test. Alarms created during a test
    are destroyed at the end of the test.
    """
    cfn_helper = CloudFormationTemplate(boto3_session)
    s3_helper = S3(boto3_session)
    unique_suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=4))
    manager = AlarmManager(unique_suffix, boto3_session, cfn_helper, s3_helper)
    yield manager
    manager.destroy_deployed_alarms()


def get_boto3_session(aws_profile):
    '''
    Helper to create boto3 session based on given AWS profile.
    :param The AWS profile name.
    '''
    logging.info("Creating boto3 session for [{}] profile.".format(aws_profile))
    return boto3.Session(profile_name=aws_profile)


@given(parse('published "{ssm_document_name}" SSM document'))
def publish_ssm_document(boto3_session, ssm_document_name):
    """
    Publish SSM document using 'publisher.publish_documents.PublishDocuments'.
    :param boto3_session The boto3 session
    :param ssm_document_name The SSM document name
    """
    p = PublishDocuments(boto3_session)
    documents_metadata = p.get_documents_list_by_names([ssm_document_name])
    p.publish_document(documents_metadata)


@given(parse('the cloud formation templates as integration test resources\n{cfn_input_parameters}'))
def set_up_cfn_template_resources(resource_pool, cfn_input_parameters, ssm_test_cache):
    """
    Common step to specify cloud formation template with parameters for specific test. It can be reused with no
    need to define this step implementation for every test. However it should be mentioned in your feature file.
    Example you can find in: .../documents/rds/test/force_aurora_failover/Tests/features/aurora_failover_cluster.feature
    :param resource_pool: The resource pool which will take care of managing given template deployment
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
        rm_resource_type = ResourceModel.ResourceType.from_string(resource_type)
        resource_pool.add_cfn_template(cf_template_path, rm_resource_type, **cf_input_params)


@when(parse('SSM automation document "{ssm_document_name}" executed\n{ssm_input_parameters}'))
@given(parse('SSM automation document "{ssm_document_name}" executed\n{ssm_input_parameters}'))
@then(parse('SSM automation document "{ssm_document_name}" executed\n{ssm_input_parameters}'))
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

    _put_ssm_execution_id_in_test_cache(execution_id, ssm_test_cache)
    return execution_id


def _put_ssm_execution_id_in_test_cache(execution_id, ssm_test_cache):
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


@given(parse('SSM automation document "{ssm_document_name}" execution in status "{expected_status}"'
             '\n{input_parameters}'))
@when(parse('SSM automation document "{ssm_document_name}" execution in status "{expected_status}"'
            '\n{input_parameters}'))
@then(parse('SSM automation document "{ssm_document_name}" execution in status "{expected_status}"'
            '\n{input_parameters}'))
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


wait_for_execution_step_with_params_description = \
    'Wait for the SSM automation document "{ssm_document_name}" execution is on step "{ssm_step_name}" ' \
    'in status "{expected_status}" for "{time_to_wait}" seconds\n{input_parameters}'


@when(parse(wait_for_execution_step_with_params_description))
@then(parse(wait_for_execution_step_with_params_description))
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

    int_time_to_wait = int(time_to_wait)
    logging.info(f'Waiting for {expected_status} status of {ssm_step_name} step in {ssm_document_name} document '
                 f'during {int_time_to_wait} seconds')
    if expected_status == 'InProgress':
        actual_status = ssm_document.wait_for_execution_step_status_is_in_progress(
            ssm_execution_id, ssm_document_name, ssm_step_name, int_time_to_wait
        )
    else:
        actual_status = ssm_document.wait_for_execution_step_status_is_terminal_or_waiting(
            ssm_execution_id, ssm_document_name, ssm_step_name, int_time_to_wait
        )
    assert expected_status == actual_status


@given(parse('the cached input parameters\n{input_parameters}'))
def given_cached_input_parameters(ssm_test_cache, input_parameters):
    for parm_name, param_val in parse_str_table(input_parameters).rows[0].items():
        ssm_test_cache[parm_name] = str(param_val)


@then(parse('terminate "{ssm_document_name}" SSM automation document\n{input_parameters}'))
def terminate_ssm_execution(boto3_session, cfn_output_params, ssm_test_cache, ssm_document, input_parameters):
    ssm = boto3_session.client('ssm')
    parameters = ssm_document.parse_input_parameters(cfn_output_params, ssm_test_cache, input_parameters)
    ssm.stop_automation_execution(AutomationExecutionId=parameters['ExecutionId'][0], Type='Cancel')


@given(parse('sleep for "{seconds}" seconds'))
@when(parse('sleep for "{seconds}" seconds'))
@then(parse('sleep for "{seconds}" seconds'))
def sleep_seconds(seconds):
    # Need to wait for more than 5 minutes for metric to be reported
    logging.info('Sleeping for [{}] seconds'.format(seconds))
    time.sleep(int(seconds))


@given(parse('assert SSM automation document step "{step_name}" execution in status "{expected_step_status}"'
             '\n{parameters}'))
@when(parse('assert SSM automation document step "{step_name}" execution in status "{expected_step_status}"'
            '\n{parameters}'))
@then(parse('assert SSM automation document step "{step_name}" execution in status "{expected_step_status}"'
            '\n{parameters}'))
def verify_step_in_status(boto3_session, step_name, expected_step_status, ssm_test_cache, parameters):
    params = parse_param_values_from_table(parameters, {'cache': ssm_test_cache})
    current_step_status = get_ssm_step_status(boto3_session, params[0]['ExecutionId'], step_name)
    assert expected_step_status == current_step_status


@when(parse('assert "{metric_name}" metric point "{operator}" than "{exp_perc}" percent(s)\n{input_params}'))
@then(parse('assert "{metric_name}" metric point "{operator}" than "{exp_perc}" percent(s)\n{input_params}'))
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


@when(parse('Approve SSM automation document on behalf of the role\n{input_parameters}'))
def approve_automation(cfn_output_params, ssm_test_cache, boto3_session, input_parameters):
    """
    Common step to approve waiting execution
    :param cfn_output_params The cfn output params from resource manager
    :param ssm_test_cache The custom test cache
    :param boto3_session Base boto3 session
    :param input_parameters The input parameters
    """
    parameters = parse_param_values_from_table(input_parameters, {'cache': ssm_test_cache,
                                                                  'cfn-output': cfn_output_params})
    ssm_execution_id = parameters[0].get('ExecutionId')
    role_arn = parameters[0].get('RoleArn')
    if ssm_execution_id is None:
        raise Exception('Parameter with name [ExecutionId] should be provided')
    if role_arn is None:
        raise Exception('Parameter with name [RoleArn] should be provided')
    assumed_role_session = assume_role_session(role_arn, boto3_session)
    send_step_approval(assumed_role_session, ssm_execution_id)


@when(parse('Reject SSM automation document on behalf of the role\n{input_parameters}'))
def reject_automation(cfn_output_params, ssm_test_cache, boto3_session, input_parameters):
    """
    Common step to reject waiting execution
    :param cfn_output_params The cfn output params from resource manager
    :param ssm_test_cache The custom test cache
    :param boto3_session Base boto3 session
    :param input_parameters The input parameters
    """
    parameters = parse_param_values_from_table(input_parameters, {'cache': ssm_test_cache,
                                                                  'cfn-output': cfn_output_params})
    ssm_execution_id = parameters[0].get('ExecutionId')
    role_arn = parameters[0].get('RoleArn')
    if ssm_execution_id is None:
        raise Exception('Parameter with name [ExecutionId] should be provided')
    if role_arn is None:
        raise Exception('Parameter with name [RoleArn] should be provided')
    assumed_role_session = assume_role_session(role_arn, boto3_session)
    send_step_approval(assumed_role_session, ssm_execution_id, is_approved=False)


@given(parse('cache constant value {value} as "{cache_property}" '
             '"{step_key}" SSM automation execution'))
def cache_expected_constant_value_before_ssm(ssm_test_cache, value, cache_property, step_key):
    param_value = parse_param_value(value, {'cache': ssm_test_cache})
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, str(param_value))


@then(parse('cache rollback execution id\n{input_parameters}'))
def cache_rollback_execution_id(ssm_document, ssm_test_cache, input_parameters):
    parameters = parse_param_values_from_table(input_parameters, {'cache': ssm_test_cache,
                                                                  'cfn-output': cfn_output_params})
    ssm_execution_id = parameters[0].get('ExecutionId')
    _put_ssm_execution_id_in_test_cache(ssm_document.get_step_output(
        ssm_execution_id, 'TriggerRollback', 'RollbackExecutionId'), ssm_test_cache)


@when(parse('cache execution output value of "{target_property}" as "{cache_property}" after SSM automation execution'
            '\n{input_parameters}'))
def cache_execution_output_value(ssm_test_cache, boto3_session, target_property, cache_property, input_parameters):
    execution_id = parse_param_values_from_table(input_parameters, {
        'cache': ssm_test_cache,
        'cfn-output': cfn_output_params})[0].get('ExecutionId')
    target_property_value = get_ssm_execution_output_value(boto3_session, execution_id, target_property)
    put_to_ssm_test_cache(ssm_test_cache, "after", cache_property, target_property_value)


@when(parse('Wait for alarm to be in state "{alarm_state}" for "{timeout}" seconds\n{input_parameters}'))
@then(parse('Wait for alarm to be in state "{alarm_state}" for "{timeout}" seconds\n{input_parameters}'))
def wait_for_alarm(cfn_output_params, cfn_installed_alarms, ssm_test_cache, boto3_session, alarm_state, timeout,
                   input_parameters):
    parameters = parse_param_values_from_table(input_parameters, {'cache': ssm_test_cache,
                                                                  'cfn-output': cfn_output_params,
                                                                  'alarm': cfn_installed_alarms})
    alarm_name = parameters[0].get('AlarmName')
    if alarm_name is None:
        raise Exception('Parameter with name [AlarmName] should be provided')
    time_to_wait = int(timeout)
    wait_for_metric_alarm_state(boto3_session, alarm_name, alarm_state, time_to_wait)


@given(parse('Wait until alarm {alarm_name_ref} becomes OK within {wait_sec} seconds, '
             'check every {delay_sec} seconds'))
@then(parse('Wait until alarm {alarm_name_ref} becomes OK within {wait_sec} seconds, '
            'check every {delay_sec} seconds'))
def wait_until_alarm_green(alarm_name_ref: str, wait_sec: str, delay_sec: str, cfn_installed_alarms: dict,
                           cfn_output_params: dict, ssm_test_cache: dict, boto3_session: boto3.Session):
    alarm_name = parse_param_value(alarm_name_ref, {'cfn-output': cfn_output_params,
                                                    'cache': ssm_test_cache,
                                                    'alarm': cfn_installed_alarms})
    alarm_state = AlarmState.INSUFFICIENT_DATA
    wait_sec = int(wait_sec)
    delay_sec = int(delay_sec)
    logging.info('Inputs:'
                 f'alarm_name:{alarm_name};'
                 f'alarm_state:{alarm_state};'
                 f'wait_sec:{wait_sec};'
                 f'delay_sec:{delay_sec};')

    elapsed = 0
    iteration = 1
    while elapsed < wait_sec:
        start = time.time()
        alarm_state = get_metric_alarm_state(session=boto3_session,
                                             alarm_name=alarm_name)
        logging.info(f'#{iteration}; Alarm:{alarm_name}; State: {alarm_state};'
                     f'Elapsed: {elapsed} sec;')
        if alarm_state == AlarmState.OK:
            return
        time.sleep(delay_sec)
        end = time.time()
        elapsed += (end - start)
        iteration += 1

    raise TimeoutError(f'After {wait_sec} alarm {alarm_name} is in {alarm_state} state;'
                       f'Elapsed: {elapsed} sec;'
                       f'{iteration} iterations;')


# Alarm
@given(parse('alarm "{alarm_reference_id}" is installed\n{input_parameters_table}'))
@when(parse('alarm "{alarm_reference_id}" is installed\n{input_parameters_table}'))
@then(parse('alarm "{alarm_reference_id}" is installed\n{input_parameters_table}'))
def install_alarm_from_reference_id(alarm_reference_id, input_parameters_table,
                                    alarm_manager, ssm_test_cache, cfn_output_params):
    input_params = {name: parse_param_value(val, {'cache': ssm_test_cache,
                                                  'cfn-output': cfn_output_params})
                    for name, val in
                    parse_str_table(input_parameters_table).rows[0].items()}

    alarm_manager.deploy_alarm(alarm_reference_id, input_params)


@then(parse('assert metrics for all alarms are populated'))
def verify_alarm_metrics_exist_defaults(alarm_manager):
    verify_alarm_metrics_exist(alarm_manager, 300, 15)


@then(parse('assert metrics for all alarms are populated within {wait_sec:d} seconds, '
            'check every {delay_sec:d} seconds'))
def verify_alarm_metrics_exist(alarm_manager, wait_sec, delay_sec):
    elapsed = 0
    iteration = 1
    while elapsed < wait_sec:
        start = time.time()
        alarms_missing_data = alarm_manager.collect_alarms_without_data(wait_sec)
        if not alarms_missing_data:
            return  # All alarms have data
        logging.info(f'#{iteration}; Alarms missing data: {alarms_missing_data} '
                     f'Elapsed: {elapsed} sec;')
        time.sleep(delay_sec)
        end = time.time()
        elapsed += (end - start)
        iteration += 1

    raise TimeoutError(f'After {wait_sec} the following alarms metrics have no data: {alarms_missing_data}'
                       f'Elapsed: {elapsed} sec;'
                       f'{iteration} iterations;')


@when(parse('wait "{metric_name}" metric point "{operator}" to "{expected_datapoint}" "{metric_unit}"\n{input_params}'))
@then(parse('wait "{metric_name}" metric point "{operator}" to "{expected_datapoint}" "{metric_unit}"\n{input_params}'))
def wait_for_metric_datapoint(metric_name, operator, expected_datapoint, cfn_output_params,
                              input_params, ssm_test_cache, metric_unit, boto3_session):
    """
    Asserts if particular metric reached desired point.
    :param expected_datapoint The expected metric point
    :param cfn_output_params The cfn output parameters from resource manager
    :param input_params The input parameters from step definition
    :param ssm_test_cache The test cache
    :param boto3_session The boto3 session
    :param metric_name The metric name to assert
    :param metric_unit The metric unit
    :param operator The operator to use for assertion
    """
    params = parse_param_values_from_table(input_params, {'cfn-output': cfn_output_params, 'cache': ssm_test_cache})
    input_param_row = params[0]
    start_time = input_param_row.pop('StartTime')
    # It is possible end time is not given
    end_time = input_param_row.pop('EndTime') if input_param_row.get('EndTime') else None
    metric_namespace = input_param_row.pop('Namespace')
    metric_period = int(input_param_row.pop('MetricPeriod'))
    metric_dimensions = input_param_row
    wait_for_metric_data_point(session=boto3_session,
                               name=metric_name,
                               datapoint_threshold=float(expected_datapoint),
                               operator=Operator.from_string(operator),
                               start_time_utc=start_time,
                               end_time_utc=end_time,
                               namespace=metric_namespace,
                               period=metric_period,
                               dimensions=metric_dimensions,
                               unit=metric_unit)


@when(parse('cache ssm step execution interval\n{input_params}'))
@then(parse('cache ssm step execution interval\n{input_params}'))
def cache_ssm_step_interval(boto3_session, input_params, cfn_output_params, ssm_test_cache):
    params = parse_param_values_from_table(input_params, {'cfn-output': cfn_output_params, 'cache': ssm_test_cache})
    input_param_row = params[0]
    execution_id = input_param_row.get('ExecutionId')
    step_name = input_param_row.get('StepName')
    if not execution_id or not step_name:
        raise Exception('Parameters [ExecutionId] and [StepName] should be presented.')
    exec_start, exec_end = get_ssm_step_interval(boto3_session, execution_id, step_name)
    execution_id_ref = parse_str_table(input_params).rows[0]['ExecutionId']
    ssm_execution_id = re.search(r'SsmExecutionId>\d+', execution_id_ref).group().split('>')[1]
    ssm_test_cache['SsmStepExecutionInterval'] = {ssm_execution_id: {step_name: {'StartTime': exec_start,
                                                                                 'EndTime': exec_end}}}
