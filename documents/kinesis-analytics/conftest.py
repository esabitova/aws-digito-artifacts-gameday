from pytest_bdd import (
    given,
    parsers, when, then
)
import pytest
import logging
from random import choices
import string

from resource_manager.src.util import kinesis_analytics_utils as kinan_utils
from resource_manager.src.util.common_test_utils import extract_param_value
from resource_manager.src.util.common_test_utils import put_to_ssm_test_cache
from resource_manager.src.util.boto3_client_factory import client
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# cache alarm Id dimension value:
cache_kinesis_application_parameters_expression = 'cache Kinesis Data Analytics for "{app_type}" application ' \
                                                  'InputId as KinesisAnalyticsInputId and OutputId as ' \
                                                  'KinesisAnalyticsOutputId "{step_key}" SSM automation execution' \
                                                  '\n{input_parameters}'


@given(parsers.parse(cache_kinesis_application_parameters_expression))
@when(parsers.parse(cache_kinesis_application_parameters_expression))
@then(parsers.parse(cache_kinesis_application_parameters_expression))
def cache_kinesis_analytics_application_parameters(resource_pool, ssm_test_cache, boto3_session,
                                                   app_type, step_key, input_parameters):
    """
    Cache demand for alarm dimensions parameters:
    :InputId and OutputId for SQL application
    :input stream Id and output stream id for Apache Flink application
    """
    kinesis_analytics_application_name = extract_param_value(
        input_parameters, 'KinesisAnalyticsApplicationName', resource_pool, ssm_test_cache)
    kinesis_analytics_input_id, kinesis_analytics_output_id = kinan_utils.cache_kinan_app_seperate_flink_sql(
        kinesis_analytics_application_name, app_type, boto3_session)
    put_to_ssm_test_cache(ssm_test_cache, step_key, 'KinesisAnalyticsInputId', kinesis_analytics_input_id)
    put_to_ssm_test_cache(ssm_test_cache, step_key, 'KinesisAnalyticsOutputId', kinesis_analytics_output_id)


# create s3 bucket for kinesis data analytics apache flink application file and teradown it after test:
create_s3_bucket_for_kinesis_analytics_application_expression = 'create S3 bucket and save the bucket name ' \
                                                                'as "{bucket_cache_name}" to "{cache_property}" ' \
                                                                'cache property' \
                                                                '\n{input_parameters}'


@given(parsers.parse(create_s3_bucket_for_kinesis_analytics_application_expression))
def create_s3_bucket_for_kinesis_analytics_application(resource_pool, ssm_test_cache, boto3_session,
                                                       eliminate_s3_bucket_with_object,
                                                       bucket_cache_name, cache_property, input_parameters):
    s3_client = client('s3', boto3_session)
    bucket_prefix_name = extract_param_value(
        input_parameters, 'S3BucketNamePrefix', resource_pool, ssm_test_cache)
    account_id = boto3_session.client('sts').get_caller_identity().get('Account')
    region_name = boto3_session.region_name
    random_postfix = ''.join(choices(string.ascii_lowercase + string.digits, k=6))

    bucket_name = bucket_prefix_name + "-" + account_id + "-" + region_name + "-" + random_postfix
    try:
        if region_name == 'us-east-1':
            s3_client.create_bucket(ACL='private', Bucket=bucket_name)
        else:
            s3_client.create_bucket(ACL='private', Bucket=bucket_name, CreateBucketConfiguration={
                'LocationConstraint': region_name
            })
        logger.info(f"Bucket with name [{bucket_name}] for region [{region_name}] created")
    except ClientError as ee:
        if ee.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
            logger.warning(f"Bucket with name [{bucket_name}] for region [{region_name}] already exist.")
        else:
            raise ee
    s3_client.put_bucket_versioning(Bucket=bucket_name, VersioningConfiguration={'Status': 'Enabled'})
    put_to_ssm_test_cache(ssm_test_cache, cache_property, bucket_cache_name, bucket_name)
    # teardown s3 bucket resource:
    commit_s3_bucket_teardown = extract_param_value(
        input_parameters, 'S3BucketTeardown', resource_pool, ssm_test_cache)
    eliminate_s3_bucket_with_object['bucket_name'] = bucket_name
    eliminate_s3_bucket_with_object['account_id'] = account_id
    eliminate_s3_bucket_with_object['S3BucketTeardown'] = commit_s3_bucket_teardown


# upload kinesis data analytics apache flink application to s3 bucket:
upload_kinesis_analytics_application_file_to_s3_bucket_expression = 'upload Kinesis Data Analytics application file ' \
                                                                    'to S3 bucket with given key and save locations ' \
                                                                    'to "{cache_property}" cache property' \
                                                                    '\n{input_parameters}'


@given(parsers.parse(upload_kinesis_analytics_application_file_to_s3_bucket_expression))
def upload_file_to_kinesis_analytics_s3(resource_pool, ssm_test_cache, boto3_session,
                                        cache_property, input_parameters):
    file_rel_path = extract_param_value(
        input_parameters, 'FlinkAppRelativePath', resource_pool, ssm_test_cache)
    s3_key = extract_param_value(
        input_parameters, 'FlinkAppS3Key', resource_pool, ssm_test_cache)
    bucket_name = extract_param_value(
        input_parameters, 'S3KinesisAnalyticsApplicationBucketName', resource_pool, ssm_test_cache)
    s3_client = client('s3', boto3_session)
    logging.info('Uploading file [%s] to S3 bucket [%s]', file_rel_path, bucket_name)
    with open(file_rel_path, 'rb') as file:
        file_upload_to_s3 = s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=file
        )
    version_id = file_upload_to_s3['VersionId']
    url = s3_client.generate_presigned_url(
        'get_object', Params={
            'Bucket': bucket_name,
            'Key': s3_key},
        ExpiresIn=3600)
    logging.info(f'File uploaded: url = {url}, bucket_name = {bucket_name}, object_key = {s3_key}, '
                 f'version_id = {version_id}')
    put_to_ssm_test_cache(ssm_test_cache, cache_property, 'S3ObjectVersion', version_id)
    put_to_ssm_test_cache(ssm_test_cache, cache_property, 'URI', url)
    put_to_ssm_test_cache(ssm_test_cache, cache_property, 'S3Key', s3_key)
    put_to_ssm_test_cache(ssm_test_cache, cache_property, 'S3Bucket', bucket_name)


# use next expression to test SQL application:
populate_input_stream_with_dummy_ml_data_expression = 'populate input stream with random ml data ' \
                                                      'for "{sec_interval}" seconds' \
                                                      '\n{input_parameters}'


@given(parsers.parse(populate_input_stream_with_dummy_ml_data_expression))
@when(parsers.parse(populate_input_stream_with_dummy_ml_data_expression))
@then(parsers.parse(populate_input_stream_with_dummy_ml_data_expression))
def populate_stream_with_mldata(resource_pool, ssm_test_cache, boto3_session, sec_interval, input_parameters):
    """
    Populate input stream with random 2D data.
    This is a conventional AWS example for SQL applications test
    """
    input_stream_name = extract_param_value(
        input_parameters, 'InputStreamName', resource_pool, ssm_test_cache)
    kinan_utils.generate_ml_stream(input_stream_name, sec_interval, boto3_session)


# use next expression to test Flink application:
populate_input_stream_with_dummy_ticker_data_expression = 'populate input stream with random ticker data ' \
                                                          'for "{sec_interval}" seconds' \
                                                          '\n{input_parameters}'


@given(parsers.parse(populate_input_stream_with_dummy_ticker_data_expression))
@when(parsers.parse(populate_input_stream_with_dummy_ticker_data_expression))
@then(parsers.parse(populate_input_stream_with_dummy_ticker_data_expression))
def populate_stream_with_dummy_ticker_data(resource_pool, ssm_test_cache, boto3_session, sec_interval,
                                           input_parameters):
    """
    Populate input stream with dummy ticker data
    This is a conventional AWS example for Flink applications test
    """
    input_stream_name = extract_param_value(
        input_parameters, 'InputStreamName', resource_pool, ssm_test_cache)
    kinan_utils.generate_dummy_ticker_stream(input_stream_name, sec_interval, boto3_session)


# invoke lambda loader to populate input stream:
populate_input_stream_by_dummy_ticker_lambda_loader_expression = 'populate input stream by lambda ' \
                                                                 'loader "{invoke_attempts:d}" times' \
                                                                 '\n{input_parameters}'


@given(parsers.parse(populate_input_stream_by_dummy_ticker_lambda_loader_expression))
@when(parsers.parse(populate_input_stream_by_dummy_ticker_lambda_loader_expression))
@then(parsers.parse(populate_input_stream_by_dummy_ticker_lambda_loader_expression))
def populate_input_stream_by_dummy_ticker_lambda_loader(resource_pool, ssm_test_cache,
                                                        boto3_session, invoke_attempts,
                                                        input_parameters):
    input_stream_lambda_loader_name = extract_param_value(
        input_parameters, 'InputStreamLambdaLoaderName', resource_pool, ssm_test_cache)
    kinan_utils.trigger_input_stream_lambda_loader_several_times(
        input_stream_lambda_loader_name, invoke_attempts, boto3_session)


# start kinesis analytics expression:
start_kinesis_analytics_application_expression = 'start Kinesis Data Analytics for "{app_type}" application' \
                                                 '\n{input_parameters}'


@given(parsers.parse(start_kinesis_analytics_application_expression))
@when(parsers.parse(start_kinesis_analytics_application_expression))
@then(parsers.parse(start_kinesis_analytics_application_expression))
def start_kinesis_analytics_application(resource_pool, ssm_test_cache, boto3_session,
                                        stop_kinesis_data_analytics_application,
                                        app_type, input_parameters):
    """
    starts Kinesis Data Analytics application (either sql or flink)
    """
    kinesis_analytics_application_name = extract_param_value(input_parameters,
                                                             'KinesisAnalyticsAppName', resource_pool,
                                                             ssm_test_cache)
    kinesis_analytics_input_id = None
    if app_type in ['sql', 'Sql', 'SQL']:
        kinesis_analytics_input_id = extract_param_value(input_parameters,
                                                         'KinesisAnalyticsInputId', resource_pool, ssm_test_cache)
    kinan_utils.start_kinesis_analytics_app(kinesis_analytics_application_name,
                                            kinesis_analytics_input_id, app_type, boto3_session)
    stop_kinesis_data_analytics_application['app_name'] = kinesis_analytics_application_name


# kinesis application shut down:
shut_down_kinesis_analytics_app_expression = 'shut down Kinesis Data Analytics application' \
                                             '\n{input_parameters}'


@then(parsers.parse(shut_down_kinesis_analytics_app_expression))
def application_shut_down(resource_pool, ssm_test_cache, boto3_session, input_parameters):
    """
    stops Kinesis Data Analytics application (either sql or flink)
    force stops kinesis analytics expression if simple stop fails
    """
    kinesis_analytics_application_name = extract_param_value(input_parameters,
                                                             'KinesisAnalyticsAppName', resource_pool,
                                                             ssm_test_cache)
    kinan_utils.stop_kinesis_analytics_app(kinesis_analytics_application_name, boto3_session)


# kinesis data analytics snapshots list cache expression:
cache_existing_snapshots_kinan_application = 'cache existing snapshots of Flink application as ' \
                                             '"{snapshots_list_name}" "{step_key}" SSM automation execution' \
                                             '\n{input_parameters}'


@given(parsers.parse(cache_existing_snapshots_kinan_application))
@when(parsers.parse(cache_existing_snapshots_kinan_application))
@then(parsers.parse(cache_existing_snapshots_kinan_application))
def cache_existing_snapshots_kinesis_analytics_app(resource_pool, ssm_test_cache, boto3_session, snapshots_list_name,
                                                   step_key, input_parameters):
    kinesis_analytics_application_name = extract_param_value(input_parameters,
                                                             'KinesisAnalyticsAppName', resource_pool,
                                                             ssm_test_cache)
    kinesis_analytics_snapshots_list = kinan_utils.cache_kinan_app_snapshpots_list(
        kinesis_analytics_application_name, boto3_session)
    put_to_ssm_test_cache(ssm_test_cache, step_key, snapshots_list_name, kinesis_analytics_snapshots_list)


# prove snapshot exist or create it otherwise:
prove_kinesis_data_analytics_snapshot_exist_expression = 'prove recovery snapshot exists and confect it otherwise'\
                                                         '\n{input_parameters}'


@given(parsers.parse(prove_kinesis_data_analytics_snapshot_exist_expression))
@when(parsers.parse(prove_kinesis_data_analytics_snapshot_exist_expression))
@then(parsers.parse(prove_kinesis_data_analytics_snapshot_exist_expression))
def prove_kda_snapshot_exist_or_create(resource_pool, ssm_test_cache,
                                       boto3_session, eliminate_test_snapshot,
                                       input_parameters):
    kinesis_analytics_application_name = extract_param_value(input_parameters,
                                                             'KinesisAnalyticsAppName', resource_pool,
                                                             ssm_test_cache)
    snapshot_name_to_prove = extract_param_value(input_parameters,
                                                 'KinesisAnalyticsInputSnapshotName', resource_pool,
                                                 ssm_test_cache)
    # "teardown_snapshot_name" will be different from initial "snapshot_name_to_prove",
    # if "snapshot_name_to_prove" was "Latest"
    create_snapshot, teardown_snapshot_name = kinan_utils.prove_snapshot_exist_or_confect(
        kinesis_analytics_application_name, snapshot_name_to_prove, boto3_session)
    # if snapshot did not exist, and we createed a new one, must teardown it:
    if create_snapshot:
        eliminate_test_snapshot['KinesisAnalyticsAppName'] = kinesis_analytics_application_name
        eliminate_test_snapshot['NewSnapshotName'] = teardown_snapshot_name
        eliminate_test_snapshot['Teardown'] = 'Yes'


# cache kinesis analytics new snapshot name expression:
cache_kinan_application_new_snapshot_name_expression = 'provide Kinesis Analytics application new snapshot ' \
                                                       'name as "{cache_name_new_snapshot}" and save ' \
                                                       'locations to "{cache_property}" cache property' \
                                                       '\n{input_parameters}'


@given(parsers.parse(cache_kinan_application_new_snapshot_name_expression))
@when(parsers.parse(cache_kinan_application_new_snapshot_name_expression))
@then(parsers.parse(cache_kinan_application_new_snapshot_name_expression))
def cache_kinesis_analytics_application_new_snapshot_name(resource_pool, ssm_test_cache, boto3_session,
                                                          eliminate_test_snapshot, cache_name_new_snapshot,
                                                          cache_property, input_parameters):
    kinesis_analytics_application_name = extract_param_value(input_parameters,
                                                             'KinesisAnalyticsAppName', resource_pool,
                                                             ssm_test_cache)
    try:
        input_snapshot_name = extract_param_value(input_parameters,
                                                  'KinesisAnalyticsInputSnapshotName', resource_pool,
                                                  ssm_test_cache)
    except Exception:
        input_snapshot_name = None
    try:
        commit_teardown = extract_param_value(input_parameters,
                                              'Teardown', resource_pool, ssm_test_cache)
    except Exception:
        commit_teardown = 'No'
    new_snapshot_name = kinan_utils.provide_test_snapshot_name(kinesis_analytics_application_name,
                                                               input_snapshot_name)
    put_to_ssm_test_cache(ssm_test_cache, cache_property, cache_name_new_snapshot, new_snapshot_name)
    eliminate_test_snapshot['KinesisAnalyticsAppName'] = kinesis_analytics_application_name
    eliminate_test_snapshot['NewSnapshotName'] = new_snapshot_name
    eliminate_test_snapshot['Teardown'] = commit_teardown


# cache kinesis analytics running application snapshot name (if any):
cache_running_kinesis_analytics_application_snapshot_expression = 'cache kinesis data analytics application ' \
                                                                  'running snapshot as "{cache_name_app_snapshot}" '\
                                                                  '"{step_key}" SSM automation execution' \
                                                                  '\n{input_parameters}'


@given(parsers.parse(cache_running_kinesis_analytics_application_snapshot_expression))
@when(parsers.parse(cache_running_kinesis_analytics_application_snapshot_expression))
@then(parsers.parse(cache_running_kinesis_analytics_application_snapshot_expression))
def cache_running_kinesis_analytics_app_snapshot(resource_pool, ssm_test_cache, boto3_session,
                                                 cache_name_app_snapshot, step_key, input_parameters):
    kinesis_analytics_application_name = extract_param_value(input_parameters,
                                                             'KinesisAnalyticsAppName', resource_pool,
                                                             ssm_test_cache)
    app_snapshot_name = kinan_utils.extract_running_app_snapshot_name(kinesis_analytics_application_name,
                                                                      boto3_session)
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_name_app_snapshot, app_snapshot_name)


# cache kinesis data analytics latest snapshot (if any):
cache_kinesis_analytics_latest_snapshot_expression = 'cache latest existent kinesis data analytics application ' \
                                                     'snapshot as "{cache_latest_snapshot}" and save locations ' \
                                                     'to "{cache_property}" cache property'\
                                                     '\n{input_parameters}'


@given(parsers.parse(cache_kinesis_analytics_latest_snapshot_expression))
@when(parsers.parse(cache_kinesis_analytics_latest_snapshot_expression))
@then(parsers.parse(cache_kinesis_analytics_latest_snapshot_expression))
def cache_kinesis_analytics_latest_snapshot(resource_pool, ssm_test_cache, boto3_session,
                                            cache_latest_snapshot, cache_property, input_parameters):
    kinesis_analytics_application_name = extract_param_value(input_parameters,
                                                             'KinesisAnalyticsAppName', resource_pool,
                                                             ssm_test_cache)
    latest_snapshot_name = kinan_utils.provide_latest_snapshot(kinesis_analytics_application_name,
                                                               boto3_session)
    put_to_ssm_test_cache(ssm_test_cache, cache_property, cache_latest_snapshot, latest_snapshot_name)


# cache kinesis data analytics status code data
cache_kinesis_analytics_status_code_expression = 'get Kinesis Data Analytics application status code and cache ' \
                                                 'as "{cache_status_code_property_name}" "{step_key}" '\
                                                 'SSM automation execution' \
                                                 '\n{input_parameters}'


@given(parsers.parse(cache_kinesis_analytics_status_code_expression))
@when(parsers.parse(cache_kinesis_analytics_status_code_expression))
@then(parsers.parse(cache_kinesis_analytics_status_code_expression))
def cache_kinesis_analytics_status_code(resource_pool, ssm_test_cache, boto3_session,
                                        cache_status_code_property_name, step_key, input_parameters):
    kinesis_analytics_application_name = extract_param_value(input_parameters,
                                                             'KinesisAnalyticsAppName', resource_pool,
                                                             ssm_test_cache)
    app_status_code = kinan_utils.extract_running_app_status_code(kinesis_analytics_application_name,
                                                                  boto3_session)
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_status_code_property_name, app_status_code)


# cache kinesis data analytics restore type:
cache_kinesis_data_analytics_snapshot_restore_type_expression = 'cache kinesis data analytics application ' \
                                                                'restore type as "{cache_restore_type_name}" ' \
                                                                '"{step_key}" SSM automation execution' \
                                                                '\n{input_parameters}'


@given(parsers.parse(cache_kinesis_data_analytics_snapshot_restore_type_expression))
@when(parsers.parse(cache_kinesis_data_analytics_snapshot_restore_type_expression))
@then(parsers.parse(cache_kinesis_data_analytics_snapshot_restore_type_expression))
def cache_kinesis_analytics_snapshot_restore(resource_pool, ssm_test_cache, boto3_session,
                                             cache_restore_type_name, step_key, input_parameters):
    kinesis_analytics_application_name = extract_param_value(input_parameters,
                                                             'KinesisAnalyticsAppName', resource_pool,
                                                             ssm_test_cache)
    restore_type = kinan_utils.extract_restore_type(kinesis_analytics_application_name,
                                                    boto3_session)
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_restore_type_name, restore_type)


# add kinesis data analytics application to vpc:
add_kda_application_to_vpc_expression = 'prove kinesis data analytics application is either ' \
                                        'in provided VPC or add to provided VPC otherwise' \
                                        '\n{input_parameters}'


@given(parsers.parse(add_kda_application_to_vpc_expression))
@when(parsers.parse(add_kda_application_to_vpc_expression))
@then(parsers.parse(add_kda_application_to_vpc_expression))
def add_kda_application_to_vpc_foo(resource_pool, ssm_test_cache, remove_kda_application_vpc_bind,
                                   boto3_session, input_parameters):
    kinesis_analytics_application_name = extract_param_value(
        input_parameters, 'KinesisAnalyticsAppName', resource_pool, ssm_test_cache)
    vpc_id = extract_param_value(
        input_parameters, 'VpcId', resource_pool, ssm_test_cache)
    subnet_id = extract_param_value(
        input_parameters, 'SubnetId', resource_pool, ssm_test_cache)
    security_groups_id_list = extract_param_value(
        input_parameters, 'SecurityGroupsIdList', resource_pool, ssm_test_cache)
    (remove_kda_application_vpc_bind['Teardown'],
     remove_kda_application_vpc_bind['VpcConfigurationId']) = kinan_utils.add_kda_application_to_vpc(
        kinesis_analytics_application_name, vpc_id, subnet_id, security_groups_id_list, boto3_session)
    remove_kda_application_vpc_bind['KinesisAnalyticsAppName'] = kinesis_analytics_application_name
    remove_kda_application_vpc_bind['VpcId'] = vpc_id


# cache Kinesis Data Analytics VPC security group:
cache_kinesis_data_analytics_security_group_ids_expression = 'cache Kinesis Data Analytics security group ids ' \
                                                             'and save as "{cache_security_groups_id_list}" '\
                                                             'at "{step_key}" SSM automation execution'\
                                                             '\n{input_parameters}'


@given(parsers.parse(cache_kinesis_data_analytics_security_group_ids_expression))
@when(parsers.parse(cache_kinesis_data_analytics_security_group_ids_expression))
@then(parsers.parse(cache_kinesis_data_analytics_security_group_ids_expression))
def cache_kinesis_analytics_security_group_ids(resource_pool, ssm_test_cache, boto3_session,
                                               cache_security_groups_id_list, step_key, input_parameters):
    kinesis_analytics_application_name = extract_param_value(
        input_parameters, 'KinesisAnalyticsAppName', resource_pool, ssm_test_cache)
    kda_security_group_ids = kinan_utils.get_kda_vpc_security_groups_id_list(
        kinesis_analytics_application_name, boto3_session)
    put_to_ssm_test_cache(ssm_test_cache, step_key, cache_security_groups_id_list, kda_security_group_ids)


# teardown of created snapshot:
@pytest.fixture(scope='function')
def eliminate_test_snapshot(boto3_session):
    test_snapshot_dict = {}
    yield test_snapshot_dict
    if test_snapshot_dict.get('Teardown') in ['YES', 'Yes', 'yes']:
        teardown_snapshot_name = test_snapshot_dict['NewSnapshotName']
        logger.info(f'Start cleanup for snapshot with name: {teardown_snapshot_name}.')
        kinesis_analytics_client = client('kinesisanalyticsv2', boto3_session)
        resp_list = kinesis_analytics_client.list_application_snapshots(
            ApplicationName=test_snapshot_dict['KinesisAnalyticsAppName'],
            Limit=49)
        snapshot_creation_stamp = [kk['SnapshotCreationTimestamp'] for kk in resp_list['SnapshotSummaries']
                                   if kk['SnapshotName'] == teardown_snapshot_name][0]
        snapshot_del_code = kinesis_analytics_client.delete_application_snapshot(
            ApplicationName=test_snapshot_dict['KinesisAnalyticsAppName'],
            SnapshotName=teardown_snapshot_name,
            SnapshotCreationTimestamp=snapshot_creation_stamp)['ResponseMetadata']['HTTPStatusCode']
        logger.info(f'Cleanup for snapshot with name: {teardown_snapshot_name} '
                    f'completed with code: {snapshot_del_code}')


# teardown of created s3 bucket:
@pytest.fixture(scope='function')
def eliminate_s3_bucket_with_object(boto3_session):
    test_s3_bucket_dict = {}
    yield test_s3_bucket_dict
    if test_s3_bucket_dict.get('S3BucketTeardown') in ['YES', 'Yes', 'yes']:
        bucket_name = test_s3_bucket_dict['bucket_name']
        s3_resource = boto3_session.resource('s3')
        s3_client = client('s3', boto3_session)
        account_id = test_s3_bucket_dict['account_id']
        logger.info('Deleting CF bucket with name [%s]', bucket_name)
        bucket = s3_resource.Bucket(bucket_name)
        if s3_resource.BucketVersioning(bucket_name).status == 'Enabled':
            bucket.object_versions.delete(ExpectedBucketOwner=account_id)
        else:
            bucket.objects.delete(ExpectedBucketOwner=account_id)
        s3_client.delete_bucket(Bucket=bucket_name, ExpectedBucketOwner=account_id)


# teardown of start application (i.e. stop application when test commences)
@pytest.fixture(scope='function')
def stop_kinesis_data_analytics_application(boto3_session):
    stop_application_dict = {}
    yield stop_application_dict
    application_name = stop_application_dict['app_name']
    kinan_utils.stop_kinesis_analytics_app(application_name, boto3_session)
    logger.info(f'Stopping kinesis data analytics application: {application_name}')


@pytest.fixture(scope='function')
def remove_kda_application_vpc_bind(boto3_session):
    remove_vpc_application_dict = {}
    yield remove_vpc_application_dict
    if remove_vpc_application_dict.get('Teardown') in ['YES', 'Yes', 'yes']:
        kinesis_analytics_client = client('kinesisanalyticsv2', boto3_session)
        application_name = remove_vpc_application_dict['KinesisAnalyticsAppName']
        conditional_token = kinesis_analytics_client.describe_application(
            ApplicationName=application_name, IncludeAdditionalDetails=True)
        conditional_token = conditional_token['ApplicationDetail']['ConditionalToken']
        vpc_configuration_id = remove_vpc_application_dict['VpcConfigurationId']
        logger.info(f'Excluding Kinesis Data Analytics applicstion {application_name}'
                    f'with vpc configuration id {vpc_configuration_id} from VPC.')
        kinesis_analytics_client.delete_application_vpc_configuration(
            VpcConfigurationId=vpc_configuration_id,
            ApplicationName=application_name,
            ConditionalToken=conditional_token)
        logger.info('Kinesis data analytics application: '
                    f'{remove_vpc_application_dict["KinesisAnalyticsAppName"]} '
                    f'excluded from VPC {remove_vpc_application_dict["VpcId"]}')
