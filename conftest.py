import hashlib
import logging
import os.path
import random
import re
import shutil
import string
import subprocess
import sys
import time
import unittest
import uuid
from datetime import datetime
from typing import List

import boto3
import jsonpath_ng
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
from resource_manager.src.constants import BgColors
from resource_manager.src.resource_pool import ResourcePool
from resource_manager.src.s3 import S3
from resource_manager.src.ssm_document import SsmDocument
from resource_manager.src.util import common_test_utils
from resource_manager.src.util.boto3_client_factory import client
from resource_manager.src.util.common_test_utils import put_to_ssm_test_cache
from resource_manager.src.util.cw_util import get_ec2_metric_max_datapoint, wait_for_metric_alarm_state
from resource_manager.src.util.cw_util import get_metric_alarm_state
from resource_manager.src.util.cw_util import wait_for_metric_data_point
from resource_manager.src.util.enums.alarm_state import AlarmState
from resource_manager.src.util.enums.operator import Operator
from resource_manager.src.util.param_utils import parse_param_value, parse_param_values_from_table
from resource_manager.src.util.param_utils import parse_pool_size
from resource_manager.src.util.role_session import RoleSession
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
    parser.addoption("--aws_role_arn",
                     action="store",
                     default=None,
                     help="Role for integration tests execution. If specified it will override --aws_profile and"
                          "use role credentials for tests execution.")
    parser.addoption("--keep_test_resources",
                     action="store_true",
                     default=False,
                     help="Flag to keep test resources (created by Resource Manager) after all tests. Default False.")
    parser.addoption("--release_failed_resources",
                     action="store_true",
                     default=False,
                     help="Flag to release failed test resources to the pool. Default False.")
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


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Sets test execution result to session object.
    :param item:
    :param call:
    """
    outcome = yield
    result = outcome.get_result()
    if result.when == 'call':
        item.session.test_report = result


def pytest_sessionstart(session):
    """
    Hook https://docs.pytest.org/en/stable/reference.html#initialization-hooks \n
    For this case we want to create test DDB tables before running any test.
    :param session: Tests session
    """
    # Execute when running integration tests
    if session.config.option.run_integration_tests:
        # Generating testing session id in order to tie test resources to specific session, so that when
        # running tests in parallel by multiple machines (sessions) tests will not try to change state of
        # resources which are still in use by other sessions.
        test_session_id = str(uuid.uuid4())
        session.config.option.test_session_id = test_session_id
        aws_role_arn = session.config.option.aws_role_arn
        aws_profile_name = session.config.option.aws_profile
        boto3_session = get_boto3_session(aws_profile_name, aws_role_arn)
        session.config.option.aws_account_id = boto3_session.client('sts').get_caller_identity().get('Account')

        logging.info(BgColors.OKBLUE + 'Starting testing session with following parameters:' + BgColors.ENDC)
        logging.info(BgColors.OKBLUE + f' - test session id: {test_session_id}' + BgColors.ENDC)
        logging.info(BgColors.OKBLUE + f' - aws account id: {session.config.option.aws_account_id}' + BgColors.ENDC)
        logging.info(BgColors.OKBLUE + f' - aws region: {boto3_session.region_name}' + BgColors.ENDC)
        logging.info(BgColors.OKBLUE + f' - aws profile: {aws_profile_name}' + BgColors.ENDC)
        logging.info(BgColors.OKBLUE + f' - aws role arn: {aws_role_arn}' + BgColors.ENDC)

        cfn_helper = CloudFormationTemplate(boto3_session)
        s3_helper = S3(boto3_session, session.config.option.aws_account_id)
        rm = ResourcePool(cfn_helper, s3_helper, dict(), None, None)
        rm.init_ddb_tables(boto3_session)
        # Distributed mode is considered mode when we executing integration tests on multiple testing sessions/machines
        # and targeting same AWS account resources, in this case we should not perform resource fixing, since it
        # can change resources state which is in use by other session.
        if not session.config.option.distributed_mode:
            rm.fix_stalled_resources()


def pytest_sessionfinish(session, exitstatus):
    """
    Hook https://docs.pytest.org/en/stable/reference.html#initialization-hooks \n
    :param session: The pytest session object.
    :param exitstatus: (int) The status which pytest will return to the system.
    :return:
    """
    # Execute only when running integration tests and disabled skip session level hooks
    # In case we do execute tests not in single session, for example in different machines, we don't want
    # to perform resource fix/destroy since one session can try to modify resource state which is used
    # by another session.At this moment this case is used on CodeCommit pipeline actions where we do
    # execute tests in parallel on different machines in same AWS account.

    if session.config.option.run_integration_tests:
        test_session_id = session.config.option.test_session_id
        aws_role_arn = session.config.option.aws_role_arn
        aws_profile_name = session.config.option.aws_profile
        aws_account_id = session.config.option.aws_account_id

        boto3_session = get_boto3_session(aws_profile_name, aws_role_arn)
        cfn_helper = CloudFormationTemplate(boto3_session)
        s3_helper = S3(boto3_session, aws_account_id)
        rm = ResourcePool(cfn_helper, s3_helper, dict(), test_session_id, None)
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
    """
    Creates session for given profile name. More about how to configure AWS profile:
    https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-profiles.html
    :param request The pytest request object
    """
    # Applicable only for integration tests
    if request.session.config.option.run_integration_tests:
        aws_role_arn = request.session.config.option.aws_role_arn
        aws_profile_name = request.config.option.aws_profile
        return get_boto3_session(aws_profile_name, aws_role_arn)
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
def test_name_log(request):
    """
    Returns name of the test for logging in following format:
    [test_file_name.py::test_case_name]
    :param request: The request object
    :return: The name of the test for logging
    """
    full_test_path = str(request.fspath + '::' + request.node.name)
    return full_test_path[full_test_path.rindex('/') + 1:len(full_test_path)]


@pytest.fixture(scope='function')
def function_logger(test_name_log):
    """
    Returns logger to be used in tests.
    :param test_name_log: The name of the test for logging
    :return: The logger to be used in tests.
    """
    return logging.getLogger(BgColors.OKBLUE + '[' + test_name_log + ']' + BgColors.ENDC)


@pytest.fixture(scope='function')
def resource_pool(request, boto3_session, ssm_test_cache, function_logger):
    """
    Creates ResourcePool fixture for every test case.
    :param request: The pytest request object
    :param boto3_session: The boto3 session
    :param ssm_test_cache: The ssm test cache
    :param function_logger: The function level logger
    :return: The resource pool fixture
    """

    test_session_id = request.session.config.option.test_session_id
    aws_account_id = request.session.config.option.aws_account_id

    cfn_helper = CloudFormationTemplate(boto3_session, function_logger)
    s3_helper = S3(boto3_session, aws_account_id, function_logger)
    custom_pool_size = parse_pool_size(request.session.config.option.pool_size)
    rp = ResourcePool(cfn_helper, s3_helper, custom_pool_size, test_session_id, ssm_test_cache, function_logger)
    yield rp
    # Release resources after test execution is completed if test was not manually
    # interrupted/cancelled. In case of interruption resources will be
    # released and fixed on 'pytest_sessionfinish'
    if request.session.exitstatus != ExitCode.INTERRUPTED:
        test_execution_report = request.session.test_report
        release_failed_resources = request.session.config.option.release_failed_resources
        rp.release_resources(test_execution_report, release_failed_resources)


@pytest.fixture(scope='function')
def ssm_document(request, boto3_session, ssm_test_cache, function_logger):
    """
    Creates SsmDocument fixture to for every test case.
    """
    ssm = SsmDocument(boto3_session, function_logger)
    yield ssm
    # Applicable only for integration tests
    if request.session.config.option.run_integration_tests:
        cached_executions = ssm_test_cache.get('SsmExecutionId')
        if cached_executions is not None:
            for index, execution_id in cached_executions.items():
                ssm.cancel_execution_with_rollback(execution_id)


@pytest.fixture(scope='function')
def ssm_test_cache():
    """
    Cache for test. There may be cases when state between test steps can be changed,
    but we want to remember it to be able to verify how state was changed after.
    Example you can find in: .../documents/rds/test/force_aurora_failover/Tests/features/aurora_failover_cluster.feature
    """
    cache = dict()
    return cache


@pytest.fixture
def alarm_manager(request, boto3_session, function_logger):
    """
    Container for alarms deployed during a test. Alarms created during a test
    are destroyed at the end of the test.
    """
    aws_account_id = request.session.config.option.aws_account_id
    cfn_helper = CloudFormationTemplate(boto3_session, function_logger)
    s3_helper = S3(boto3_session, aws_account_id, function_logger)
    unique_suffix = ''.join(random.Random().choices(string.ascii_letters + string.digits, k=4))
    manager = AlarmManager(unique_suffix, boto3_session, cfn_helper, s3_helper, logger=function_logger)
    yield manager
    manager.destroy_deployed_alarms()


def get_boto3_session(aws_profile_name, aws_role_arn):
    """
    Helper to create boto3 session based on given AWS profile or AWS IAM role.
    With IAM role credentials will be refreshed every time boto3 client is created as
    well as if client session is exceeding 1 hour (to avoid session expiration).
    However we need to make sure that credentials which are used to assume this role
    will not exceed session time limit as well.
    :param aws_profile_name: The AWS profile name as credential provider.
    :param aws_role_arn: The AWS IAM role arn to be used as credential provider.
    """
    # If aws_profile_name == 'no_profile' we are using
    # 'Instance metadata service on an Amazon EC2 instance that has an IAM role configured'
    #  in CodeCommit Pipeline: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html
    session = boto3.Session() if aws_profile_name == 'no_profile' else boto3.Session(profile_name=aws_profile_name)
    if aws_role_arn:
        logging.info(f"Creating boto3 session with [{aws_profile_name}] profile and [{aws_role_arn}] role credentials.")
        return RoleSession(iam_role_arn=aws_role_arn, session_name='integration_test', credential_session=session,
                           duration=3600)
    else:
        logging.info(f"Creating boto3 session with [{aws_profile_name}] profile credentials.")
        return session


@given(parse('published "{ssm_document_name}" SSM document'))
def publish_ssm_document(boto3_session, ssm_document_name, function_logger):
    """
    Publish SSM document using 'publisher.publish_documents.PublishDocuments'.
    :param boto3_session The boto3 session
    :param ssm_document_name The SSM document name
    :param function_logger The function logger
    """
    p = PublishDocuments(boto3_session, function_logger)
    documents_metadata = p.get_documents_list_by_names([ssm_document_name])
    p.publish_document(documents_metadata)


@given(parse('the cloud formation templates as integration test resources\n{cfn_templates}'))
def set_up_cfn_template_resources(resource_pool, cfn_templates):
    """
    Common step to specify cloud formation template with parameters for specific test. It can be reused with no
    need to define this step implementation for every test. However it should be mentioned in your feature file.
    Example you can find in: .../documents/rds/test/force_aurora_failover/Tests/features/aurora_failover_cluster.feature
    :param resource_pool: The resource pool which will take care of managing given template deployment
    and providing resources for tests
    :param cfn_templates: The table of parameters as input for cloud formation template
    """
    resource_pool.add_cfn_templates(cfn_templates)


@given(parse('install dependencies from requirement file, '
             'build Lambda distribution package, and save package path to "{cache_property}" cache property'
             '\n{input_parameters_table}'))
@when(parse('install dependencies from requirement file, '
            'build Lambda distribution package, and save package path to "{cache_property}" cache property'
            '\n{input_parameters_table}'))
@then(parse('install dependencies from requirement file, '
            'build Lambda distribution package, and save package path to "{cache_property}" cache property'
            '\n{input_parameters_table}'))
def create_package_with_dependencies(cache_property, input_parameters_table, ssm_test_cache):
    """
    Common step to create package for lambda with dependencies in zip archive format
    :param cache_property: The cache property when package path will be saved
    :param input_parameters_table: The table from cucumber scenario with params
    RequirementsFileRelationalPath, DirectoryWithCodePath
    :param ssm_test_cache: The custom test cache
    :return: None
    """
    input_params = {name: val for name, val in
                    parse_str_table(input_parameters_table).rows[0].items()}
    requirements_file = os.path.abspath(input_params['RequirementsFileRelationalPath'])

    # get full and relative path's for directories
    src_dir = os.path.abspath(input_params['DirectoryWithCodeRelationalPath'])
    tmp_dir = f'{os.path.abspath(".")}/.lambda_package_tmp-{uuid.uuid4().hex}'
    lambda_package_tmp_path = f"{os.path.abspath(tmp_dir)}/lambda_function"
    lambda_package_filename = f"lambda_function-{uuid.uuid4().hex}.zip"
    package_directory_relative_path = os.path.normpath(input_params['DirectoryWithCodeRelationalPath'])
    lambda_package_relative_path = f"{package_directory_relative_path}/../{lambda_package_filename}"
    lambda_package_path = f"{src_dir}/../{lambda_package_filename}"

    # create temporary directory with default permissions
    octal_permissions = 0o755
    os.mkdir(tmp_dir, octal_permissions)
    logging.info(f"Created temporary directory '{tmp_dir}'")
    # install dependencies using pip
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-t', tmp_dir, '-r', requirements_file, '--upgrade'])
    logging.info(f"Packages from '{requirements_file}' were installed.")

    # copy source code to temporary directory ignoring __pycache__
    for item in os.listdir(src_dir):
        if item == '__pycache__':
            pass
        # check that item is a file
        elif os.path.isfile(f'{src_dir}/{item}'):
            shutil.copy2(f'{src_dir}/{item}', f'{tmp_dir}/{item}')
        # check that item is a directory
        elif os.path.isdir(f'{src_dir}/{item}'):
            shutil.copytree(f'{src_dir}/{item}', f'{tmp_dir}/{item}', copy_function=shutil.copy2)
        else:
            raise Exception(f"{src_dir}/{item} is not a directory or file")
    # create .zip package
    shutil.make_archive(lambda_package_tmp_path, 'zip', tmp_dir)
    # move artifact from tmp dir
    shutil.copy2(f'{lambda_package_tmp_path}.zip', lambda_package_path)
    logging.info(f"The following content added into package: '{str(os.listdir(tmp_dir))}'")
    # delete temporary directory
    shutil.rmtree(tmp_dir)
    # cache relative path
    ssm_test_cache[cache_property] = lambda_package_relative_path
    logging.info(f"Cached ssm_test_cache[{cache_property}]: '{lambda_package_relative_path}'")


@when(parse('SSM automation document "{ssm_document_name}" executed\n{ssm_input_parameters}'))
@given(parse('SSM automation document "{ssm_document_name}" executed\n{ssm_input_parameters}'))
@then(parse('SSM automation document "{ssm_document_name}" executed\n{ssm_input_parameters}'))
def execute_ssm_automation(ssm_document, ssm_document_name, cfn_output_params, cfn_installed_alarms, ssm_test_cache,
                           ssm_input_parameters):
    """
    Common step to execute SSM document. This step can be reused by multiple scenarios.
    :param ssm_document The SSM document object for SSM manipulation (mainly execution)
    :param ssm_document_name The SSM document name
    :param cfn_output_params The resource manager object to manipulate with testing resources
    :param cfn_installed_alarms The resource manager object to manipulate with created alarms
    :param ssm_test_cache The custom test cache
    :param ssm_input_parameters The SSM execution input parameters
    """
    parameters = ssm_document.parse_input_parameters(cfn_output_params, cfn_installed_alarms, ssm_test_cache,
                                                     ssm_input_parameters)
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
                                              ssm_document, input_parameters, ssm_test_cache, test_name_log):
    """
    Common step to wait for SSM document execution completion status. This step can be reused by multiple scenarios.
    :param cfn_output_params The cfn output params from resource manager
    :param ssm_document_name The SSM document name
    :param input_parameters The input parameters
    :param expected_status The expected SSM document execution status
    :param ssm_document The SSM document object for SSM manipulation (mainly execution)
    :param ssm_test_cache The custom test cache
    :param test_name_log The name of the test for logging
    """
    parameters = parse_param_values_from_table(input_parameters, {'cache': ssm_test_cache,
                                                                  'cfn-output': cfn_output_params})
    ssm_execution_id = parameters[0].get('ExecutionId')
    __validate_ssm_execution_id(ssm_execution_id)
    actual_status = ssm_document.wait_for_execution_completion(ssm_execution_id, ssm_document_name)
    assert expected_status == actual_status, \
        f'[{test_name_log}] SSM document assertion failed ' \
        f'[{ssm_document_name}] with execution: {ssm_document.get_execution_url(ssm_execution_id)}'


@when(parse('Wait for the SSM automation document "{ssm_document_name}" execution is on step "{ssm_step_name}" '
            'in status "{expected_status}"\n{input_parameters}'))
@then(parse('Wait for the SSM automation document "{ssm_document_name}" execution is on step "{ssm_step_name}" '
            'in status "{expected_status}"\n{input_parameters}'))
def wait_for_execution_step_with_params_default_time_to_wait(cfn_output_params, ssm_document_name, ssm_step_name,
                                                             expected_status, ssm_document, input_parameters,
                                                             ssm_test_cache, test_name_log):
    time_to_wait_default = 1200
    wait_for_execution_step_with_params(cfn_output_params, ssm_document_name, ssm_step_name, time_to_wait_default,
                                        expected_status, ssm_document, input_parameters, ssm_test_cache, test_name_log)


@when(parse('Wait for the SSM automation document "{ssm_document_name}" execution is on step "{ssm_step_name}" '
            'in status "{expected_status}" for "{time_to_wait:d}" seconds\n{input_parameters}'))
@then(parse('Wait for the SSM automation document "{ssm_document_name}" execution is on step "{ssm_step_name}" '
            'in status "{expected_status}" for "{time_to_wait:d}" seconds\n{input_parameters}'))
def wait_for_execution_step_with_params(cfn_output_params, ssm_document_name, ssm_step_name, time_to_wait,
                                        expected_status, ssm_document, input_parameters, ssm_test_cache, test_name_log):
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
    :param test_name_log The name of the test for logging
    """
    parameters = parse_param_values_from_table(input_parameters, {'cache': ssm_test_cache,
                                                                  'cfn-output': cfn_output_params})
    ssm_execution_id = parameters[0].get('ExecutionId')
    __validate_ssm_execution_id(ssm_execution_id)

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
    assert expected_status == actual_status, \
        f'[{test_name_log}] SSM document step assertion failed [{ssm_document_name}>{ssm_step_name}] ' \
        f'with step execution: {ssm_document.get_execution_step_url(ssm_execution_id, ssm_step_name)}'


@given(parse('the cached input parameters\n{input_parameters}'))
def given_cached_input_parameters(ssm_test_cache, input_parameters):
    for parm_name, param_val in parse_str_table(input_parameters).rows[0].items():
        ssm_test_cache[parm_name] = str(param_val)


@when(parse('terminate "{ssm_document_name}" SSM automation document\n{input_parameters}'))
@then(parse('terminate "{ssm_document_name}" SSM automation document\n{input_parameters}'))
def terminate_ssm_execution(boto3_session, cfn_output_params, cfn_installed_alarms,
                            ssm_test_cache, ssm_document, input_parameters):
    ssm = boto3_session.client('ssm')
    parameters = ssm_document.parse_input_parameters(cfn_output_params, cfn_installed_alarms,
                                                     ssm_test_cache, input_parameters)
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
def verify_step_in_status(boto3_session, step_name, expected_step_status, ssm_test_cache,
                          parameters, test_name_log, ssm_document):
    params = parse_param_values_from_table(parameters, {'cache': ssm_test_cache})
    ssm_execution_id = params[0]['ExecutionId']
    current_step_status = get_ssm_step_status(boto3_session, ssm_execution_id, step_name)
    assert expected_step_status == current_step_status, \
        f'[{test_name_log}] SSM document step assertion failed ' \
        f'[{step_name}] with step execution: {ssm_document.get_execution_step_url(ssm_execution_id, step_name)}'


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
    __validate_ssm_execution_id(ssm_execution_id)
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
    __validate_ssm_execution_id(ssm_execution_id)
    if role_arn is None:
        raise Exception('Parameter with name [RoleArn] should be provided')
    assumed_role_session = assume_role_session(role_arn, boto3_session)
    send_step_approval(assumed_role_session, ssm_execution_id, is_approved=False)


@given(parse('cache constant value {value} as "{cache_property}" '
             '"{step_key}" SSM automation execution'))
def cache_expected_constant_value_before_ssm(ssm_test_cache, value, cache_property, step_key):
    param_value = parse_param_value(value, {'cache': ssm_test_cache,
                                            'cfn-output': cfn_output_params})
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
@then(parse('cache execution output value of "{target_property}" as "{cache_property}" after SSM automation execution'
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


@given(parse('Wait until alarm {alarm_name_ref} becomes {alarm_expected_state} within {wait_sec} seconds, '
             'check every {delay_sec} seconds'))
@then(parse('Wait until alarm {alarm_name_ref} becomes {alarm_expected_state} within {wait_sec} seconds, '
            'check every {delay_sec} seconds'))
@when(parse('Wait until alarm {alarm_name_ref} becomes {alarm_expected_state} within {wait_sec} seconds, '
            'check every {delay_sec} seconds'))
def wait_until_alarm(alarm_name_ref: str, alarm_expected_state: str, wait_sec: str, delay_sec: str,
                     cfn_installed_alarms: dict, cfn_output_params: dict,
                     ssm_test_cache: dict, boto3_session: boto3.Session):
    alarm_name = parse_param_value(alarm_name_ref, {'cfn-output': cfn_output_params,
                                                    'cache': ssm_test_cache,
                                                    'alarm': cfn_installed_alarms})
    alarm_state = AlarmState.INSUFFICIENT_DATA
    wait_sec = int(wait_sec)
    delay_sec = int(delay_sec)
    logging.info('Inputs:'
                 f'alarm_name:{alarm_name};'
                 f'alarm_expected_state:{alarm_expected_state};'
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
        if alarm_state == AlarmState[alarm_expected_state]:
            return
        time.sleep(delay_sec)
        end = time.time()
        elapsed += (end - start)
        iteration += 1

    raise TimeoutError(f'After {wait_sec} alarm {alarm_name} is in {alarm_state} state;'
                       f'Expected state: {alarm_expected_state}'
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


@then(parse('assert metrics for all alarms are populated with params\n{input_parameters_table}'))
def verify_alarm_metrics_exist_with_inputs(input_parameters_table, alarm_manager, ssm_test_cache, cfn_output_params):
    input_params = {name: parse_param_value(val, {'cache': ssm_test_cache,
                                                  'cfn-output': cfn_output_params})
                    for name, val in
                    parse_str_table(input_parameters_table).rows[0].items()}
    verify_alarm_metrics_impl(300, 15, alarm_manager, input_params)


@then(parse('assert metrics for all alarms are populated'))
def verify_alarm_metrics_exist_defaults(alarm_manager):
    # Set 1200 secs by default because most alarms need more time to be triggered
    # If the timeout is overreached 1200 secs then all asserts will be deleted from Cucumber feature file for an
    # alarm based on agreement because it makes enourmously longer builds on CI`
    verify_alarm_metrics_impl(1200, 15, alarm_manager, {})


@then(parse('assert metrics for all alarms are populated within {wait_sec:d} seconds, '
            'check every {delay_sec:d} seconds'))
def verify_alarm_metrics_exist(wait_sec, delay_sec, alarm_manager):
    verify_alarm_metrics_impl(wait_sec, delay_sec, alarm_manager, {})


def verify_alarm_metrics_impl(wait_sec, delay_sec, alarm_manager, input_params):
    elapsed = 0
    iteration = 1
    alarms_missing_data = {}
    while elapsed < wait_sec:
        start = time.time()
        alarms_missing_data = alarm_manager.collect_alarms_without_data(wait_sec, input_params)
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


@given(parse('upload file "{file_relative_path_ref}" as "{s3_key_ref}" S3 key to S3 bucket with prefix '
             '"{s3_bucket_name_prefix_ref}" and save locations to "{cache_property}" cache property'))
def upload_file_to_s3(request, boto3_session, ssm_test_cache, file_relative_path_ref, s3_key_ref,
                      s3_bucket_name_prefix_ref, cache_property):
    """
    Upload file from the disk to S3 and save its locations.
    Does it only if the same file is not present in S3
    :param request: The pytest request object
    :param boto3_session: boto3 session
    :param ssm_test_cache: The test cache
    :param file_relative_path_ref: relational path to the file
    :param s3_key_ref: future s3 key where the file will be saved
    :param s3_bucket_name_prefix_ref: s3 bucket name where the file will be saved
    :param cache_property: the name of the cache property where URI, key, bucket, object version will be saved
    :return: None
    """
    file_rel_path = parse_param_value(file_relative_path_ref, {'cache': ssm_test_cache})
    s3_key = parse_param_value(s3_key_ref, {'cache': ssm_test_cache})
    s3_bucket_name_prefix = parse_param_value(s3_bucket_name_prefix_ref, {'cache': ssm_test_cache})
    with open(file_rel_path, "rb") as file_to_check:
        data = file_to_check.read()
        md5_hash = hashlib.md5(data).hexdigest()
    aws_account_id = request.session.config.option.aws_account_id
    s3_helper = S3(boto3_session, aws_account_id)
    try:
        response = s3_helper.retrieve_object_metadata(s3_bucket_name_prefix, s3_key)
    except ClientError as err:
        if err.response['Error']['Code'] == "403" or err.response['Error']['Code'] == '404':
            response = None
        else:
            raise err

    if response and "md5hash" in response['Object']['Metadata'] \
            and response['Object']['Metadata']['md5hash'] == md5_hash:
        logging.info(f'File {s3_key} already exists in bucket {s3_bucket_name_prefix} and has exactly the same hash')
        uri = response['Uri']
        version_id = response['Object']['VersionId']
    else:
        uri, s3_bucket_name_prefix, s3_key, version_id = s3_helper.upload_local_file_to_account_unique_bucket(
            s3_key, file_rel_path, s3_bucket_name_prefix,
            metadata={'md5hash': md5_hash}
        )
    ssm_test_cache[cache_property] = {'URI': uri, 'S3Key': s3_key,
                                      'S3Bucket': s3_bucket_name_prefix, 'S3ObjectVersion': version_id}
    logging.debug(f'ssm_test_cache was updated by ssm_test_cache[{cache_property}] '
                  f'= URI: {uri}, S3Key: {s3_key}, S3Bucket: {s3_bucket_name_prefix}, S3ObjectVersion: {version_id}. '
                  f'ssm_test_cache now is {ssm_test_cache}')


@then(parse('assert "{steps_string}" steps are successfully executed in order\n{input_parameters}'))
def assert_steps_are_successfully_executed_in_order(ssm_document, ssm_test_cache, steps_string, input_parameters):
    parameters = parse_param_values_from_table(input_parameters, {'cache': ssm_test_cache})
    ssm_execution_id = parameters[0].get('ExecutionId')
    __validate_ssm_execution_id(ssm_execution_id)
    expected_steps: List = re.findall("\\w+", steps_string)
    actual_steps = ssm_document.get_successfully_executed_steps_by_order(ssm_execution_id)
    tc = unittest.TestCase()
    tc.assertListEqual(expected_steps, actual_steps)


@given(parse('calculate "{first_value}" "{operator}" "{second_value}" '
             'and cache result as "{cache_property}" "{step_key}" SSM automation execution'))
@then(parse('calculate "{first_value}" "{operator}" "{second_value}" '
            'and cache result as "{cache_property}" "{step_key}" SSM automation execution'))
def calculate_math(ssm_test_cache, first_value, operator, second_value, cache_property, step_key):
    first_value_parsed = parse_param_value(first_value, {'cache': ssm_test_cache})
    second_value_parsed = parse_param_value(second_value, {'cache': ssm_test_cache})
    if operator == '+':
        calc_result = int(first_value_parsed) + int(second_value_parsed)
    elif operator == '-':
        calc_result = int(first_value_parsed) - int(second_value_parsed)
    else:
        raise AssertionError(f"Only '+' and '-' are allowed for operations, got: {operator}")
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_property, calc_result)


def __validate_ssm_execution_id(ssm_execution_id):
    if ssm_execution_id is None:
        raise Exception('Parameter with name [ExecutionId] should be provided')


@then(parse('SSM Automation Resume for execution "{execution_id_param}" on step "{ssm_step_name_param}"'))
@when(parse('SSM Automation Resume for execution "{execution_id_param}" on step "{ssm_step_name_param}"'))
def send_resume_signal_to_execution(execution_id_param, ssm_step_name_param,
                                    ssm_test_cache, cfn_output_params, ssm_document):
    execution_id = parse_param_value(execution_id_param, {'cache': ssm_test_cache,
                                                          'cfn-output': cfn_output_params})
    ssm_step_name = parse_param_value(ssm_step_name_param, {'cache': ssm_test_cache,
                                                            'cfn-output': cfn_output_params})

    logging.info(f'Sending Resume signal to execution {execution_id} for step {ssm_step_name}')
    ssm_document.send_resume_signal(execution_id, ssm_step_name)


@when(parse('stop FIS experiment\n{input_parameters}'))
def stop_fis_experiment(boto3_session, resource_pool, ssm_test_cache, input_parameters):
    experiment_id = common_test_utils.extract_param_value(input_parameters, 'ExperimentId',
                                                          resource_pool, ssm_test_cache)
    fis_client = client('fis', boto3_session)
    fis_client.stop_experiment(
        id=experiment_id
    )


@given(parse('cache values to "{cache_key}"\n{input_parameters}'))
@when(parse('cache values to "{cache_key}"\n{input_parameters}'))
def cache_values(request, resource_pool, cfn_output_params, ssm_test_cache, cache_key, input_parameters,
                 cfn_installed_alarms):
    """
    Cache values from cfn output, alarms, input parameter table, ssm test cache
    """
    params = common_test_utils.extract_all_from_input_parameters(cfn_output_params, ssm_test_cache, input_parameters,
                                                                 cfn_installed_alarms)
    for param_name, value in params.items():
        put_to_ssm_test_cache(ssm_test_cache, cache_key, param_name, value)


@given(parse('apply "{json_path}" JSONPath '
             'and cache value as "{cache_property}" to "{cache_key}"\n{input_parameters}'))
@when(parse('apply "{json_path}" JSONPath '
            'and cache value as "{cache_property}" to "{cache_key}"\n{input_parameters}'))
def apply_json_path_and_cache_value(cfn_output_params, ssm_test_cache, cfn_installed_alarms, json_path,
                                    cache_property, cache_key, input_parameters):
    """
    Apply json_path to the Input parameter as the reference to cfn output, alarms, input parameter table,
    ssm test cache and cache value
    """
    params = common_test_utils.extract_all_from_input_parameters(cfn_output_params, ssm_test_cache, input_parameters,
                                                                 cfn_installed_alarms)
    input_value = params['Input']
    result = jsonpath_ng.parse(json_path).find(input_value)[0].value
    put_to_ssm_test_cache(ssm_test_cache, cache_key, cache_property, result)


@given(parse('register for teardown by "{teardown_fixture_name}"\n{input_parameters}'))
@when(parse('register for teardown by "{teardown_fixture_name}"\n{input_parameters}'))
def register_for_teardown_by_dynamic_fixture(request, resource_pool, teardown_fixture_name, input_parameters,
                                             cfn_output_params, ssm_test_cache,
                                             cfn_installed_alarms):
    """
    Add keys to the dict which will be used by dynamically fetched teardown fixture to clean up everything after
    Cucumber scenario.
    You can find teardown_fixture_name as a method name in the project, usually in the corresponding service folder
    :param request The pytest request object
    :param teardown_fixture_name: dynamically passed fixture name
    :param cfn_output_params The resource manager object to manipulate with testing resources
    :param cfn_installed_alarms The resource manager object to manipulate with created alarms
    :param ssm_test_cache The custom test cache
    :param input_parameters The input parameters
    :return: dict with populated keys and values for making teardown process
    """
    params = common_test_utils.extract_all_from_input_parameters(cfn_output_params, ssm_test_cache, input_parameters,
                                                                 cfn_installed_alarms)
    teardown_fixture_dict = request.getfixturevalue(teardown_fixture_name)
    for param_name, value in params.items():
        teardown_fixture_dict[param_name] = value
    logging.warning(params)


@given(parse('parse "{param_val_ref}" and cache as {cache_property}'))
def parse_string(param_val_ref, cache_property, cfn_output_params, ssm_test_cache,
                 cfn_installed_alarms):
    """
        Replaces all `{{some_value}}` substrings in a `param_val_ref` string with a values from cache/cfn-output/alarms
        example:
          if we have in cache: `ssm_test_cache['foo']['bar']="world"`
          then expression:
          `parse "hello {{cache:foo>bar}}" and cache as "HelloString"`
          will create a new cache key:
          ssm_test_cache['HelloString'] == "hello world"
        :param cfn_output_params The resource manager object to manipulate with testing resources
        :param cfn_installed_alarms The resource manager object to manipulate with created alarms
        :param ssm_test_cache The custom test cache
        :param param_val_ref: string to parse
        :param cache_property: cache variable to save to
    """
    param_val_ref_pattern = re.compile('{{2}[^}]*}{2}')
    ref_match_list = param_val_ref_pattern.findall(param_val_ref)
    res = param_val_ref
    for ref_match in ref_match_list:
        value = parse_param_value(ref_match, {'cache': ssm_test_cache,
                                              'cfn-output': cfn_output_params,
                                              'alarm': cfn_installed_alarms})
        res = res.replace(ref_match, value)
    put_to_ssm_test_cache(ssm_test_cache, None, cache_property, res)
