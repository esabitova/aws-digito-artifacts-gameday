import logging
import time
import random
from random import choices
import string
import json

from datetime import datetime, timedelta

from documents.util.scripts.src.kinesis_analytics_util import (
    obtain_conditional_token, get_kda_vpc_security_group)

from boto3 import Session
from resource_manager.src.util.boto3_client_factory import client
from botocore.exceptions import ClientError

log = logging.getLogger()

# we wait for this timeperiod for kinesis application get into "RUNNING" status:
RETRY_START_APP_PARAMETER = 360

# time.sleep constant in case of activity failure:
ORDINARY_SLEEP_INTERVAL = 10

# maximum number of snapshots on list snapshots foo:
SNAPSHOTS_QUOTA = 49

# standard mark to construct new snapshot name from scratch:
STANDARD_SNAPSHOT_NAME_MARK = 'construct_test_snapshot_name'

# number of records on trial for the input stream to Kinesis Data Analytics Flink application:
RECORDS_NUMBER_ON_TRIAL = 4


def _wait_for_status(kinesis_analytics_client, app_name, status,
                     wait_period=RETRY_START_APP_PARAMETER,
                     interval_to_sleep=ORDINARY_SLEEP_INTERVAL):
    """
    wait for Kinesis Data Application to grab given status
    """
    start_stress = datetime.utcnow()
    end_stress = start_stress + timedelta(seconds=wait_period)
    app_status = ''
    while app_status != status:
        if datetime.utcnow() > end_stress:
            logging.error(f'Kinesis Data Analytics application {app_name} '
                          f'did not achieve status {status} '
                          f'for {str(wait_period)} seconds.'
                          f'Current application status is {app_status}.')
            raise RuntimeError()
        time.sleep(interval_to_sleep)
        app_status = kinesis_analytics_client.describe_application(
            ApplicationName=app_name)['ApplicationDetail']['ApplicationStatus']
    return


def _get_hotspot(field, spot_size):
    """
    source: https://docs.aws.amazon.com/kinesisanalytics/latest/dev/app-hotspots-prepare.html
    """
    hotspot = {
        'left': field['left'] + random.random() * (field['width'] - spot_size),
        'width': spot_size,
        'top': field['top'] + random.random() * (field['height'] - spot_size),
        'height': spot_size
    }
    return hotspot


def _get_record(field, hotspot, hotspot_weight):
    """
    source: https://docs.aws.amazon.com/kinesisanalytics/latest/dev/app-hotspots-prepare.html
    """
    rectangle = hotspot if random.random() < hotspot_weight else field
    point = {
        'x': rectangle['left'] + random.random() * rectangle['width'],
        'y': rectangle['top'] + random.random() * rectangle['height'],
        'is_hot': 'Y' if rectangle == hotspot else 'N'
    }
    return {'Data': json.dumps(point), 'PartitionKey': 'partition_key'}


def _get_ticker_data():
    """
    source: https://docs.aws.amazon.com/kinesisanalytics/latest/java/gs-python-createapp.html
    """
    return {
        'event_time': datetime.utcnow().isoformat(),
        'ticker': random.choice(['AAPL', 'AMZN', 'MSFT', 'INTC', 'TBV']),
        'price': round(random.random() * 100, 2)}


def generate_ml_stream(input_stream: str, sec_interval: str, session: Session,
                       interval_among_stream_records=0.1):
    """
    Calls AWS API to get function execution time limit
    :param input_stream: Input Stream name
    :param sec_interval: period of data generation (seconds)
    :param session The boto3 session
    :return: None
    this function is for SQL application testing
    """
    kinesis_client = client('kinesis', session)
    field = {'left': 0, 'width': 10, 'top': 0, 'height': 10}
    hotspot_size = 1
    hotspot_weight = 0.2
    batch_size = 10
    points_generated = 0
    hotspot = None
    start_stress = datetime.utcnow()
    end_stress = start_stress + timedelta(seconds=float(sec_interval))
    while datetime.utcnow() < end_stress:
        if points_generated % 1000 == 0:
            hotspot = _get_hotspot(field, hotspot_size)
        records = [
            _get_record(field, hotspot, hotspot_weight) for _ in range(batch_size)]
        points_generated += len(records)
        kinesis_client.put_records(StreamName=input_stream, Records=records)
        time.sleep(interval_among_stream_records)


def generate_dummy_ticker_stream(input_stream: str, sec_interval: str, session: Session,
                                 interval_among_stream_records=1):
    """
    starts dummy ticket generartion, based on random data
    this function is for Apache Flink application testing
    :param input_stream: Input Stream name
    :param sec_interval: period of data generation (seconds)
    :param session The boto3 session
    :return: None
    """
    kinesis_client = client('kinesis', session)
    start_stress = datetime.utcnow()
    end_stress = start_stress + timedelta(seconds=float(sec_interval))
    while datetime.utcnow() < end_stress:
        data = _get_ticker_data()
        kinesis_client.put_record(
            StreamName=input_stream,
            Data=json.dumps(data),
            PartitionKey="partitionkey")
        time.sleep(interval_among_stream_records)


def produce_dummy_ticker_stream_records(input_stream: str,
                                        session: Session,
                                        number_records=RECORDS_NUMBER_ON_TRIAL,
                                        interval_among_stream_records=1):
    """
    starts dummy ticket generartion, based on random data
    and producers preassigned number of records to the stream
    this function is for Apache Flink break VPC test testing
    :param input_stream: Input Stream name
    :param number_records: number of records to generate and put to stream
    :param interval_among_stream_records - interval among records put to the stream
    :param session The boto3 session
    :return: None
    """
    kinesis_client = client('kinesis', session)
    for _ in range(number_records):
        data = _get_ticker_data()
        kinesis_client.put_record(
            StreamName=input_stream,
            Data=json.dumps(data),
            PartitionKey="partitionkey")
        time.sleep(interval_among_stream_records)
    return


def cache_kinan_app_seperate_flink_sql(application_name: str, app_type: str, session: Session):
    """
    extracts input id and output id depending on application type
    """
    kinesis_analytics_client = client('kinesisanalyticsv2', session)
    kinesis_analytics_pars = kinesis_analytics_client.describe_application(
        ApplicationName=application_name)
    kinesis_analytics_pars = kinesis_analytics_pars['ApplicationDetail']['ApplicationConfigurationDescription']
    if app_type in ['sql', 'Sql', 'SQL']:
        kinesis_analytics_pars = kinesis_analytics_pars['SqlApplicationConfigurationDescription']
        kinesis_analytics_input_id = kinesis_analytics_pars['InputDescriptions'][0]['InputId']
        kinesis_analytics_output_id = kinesis_analytics_pars['OutputDescriptions'][0]['OutputId']
    elif app_type in ['Apache Flink', 'flink', 'Flink', 'FLINK']:
        kinesis_analytics_pars = kinesis_analytics_pars['EnvironmentPropertyDescriptions']['PropertyGroupDescriptions']
        kinesis_analytics_input_id = kinesis_analytics_pars[2]['PropertyMap']['input.stream.name'].replace('-', '_')
        kinesis_analytics_output_id = kinesis_analytics_pars[1]['PropertyMap']['output.stream.name'].replace('-', '_')
    else:
        raise KeyError('At present moment Kinesis analytics application can be sql or flink only')
    return kinesis_analytics_input_id, kinesis_analytics_output_id


def start_kinesis_analytics_app(application_name: str,
                                input_id: str,
                                app_type: str,
                                session: Session,
                                sleep_interval=ORDINARY_SLEEP_INTERVAL,
                                wait_to_start=RETRY_START_APP_PARAMETER,
                                no_more_retries=False):
    """
    starts new-made kinesis analytics application
    :param application: kinesis analytics application name
    """
    kinesis_analytics_client = client('kinesisanalyticsv2', session)
    resp = kinesis_analytics_client.describe_application(ApplicationName=application_name)
    if resp['ApplicationDetail']['ApplicationStatus'] == 'RUNNING':
        return
    elif resp['ApplicationDetail']['ApplicationStatus'] == 'READY':
        for i in range(3):
            try:
                if app_type in ['sql', 'Sql', 'SQL']:
                    start_resp = kinesis_analytics_client.start_application(
                        ApplicationName=application_name,
                        RunConfiguration={'SqlRunConfigurations':
                                          [{'InputId': input_id,
                                            'InputStartingPositionConfiguration':
                                            {'InputStartingPosition': 'NOW'}}, ]})
                elif app_type in ['Apache Flink', 'flink', 'Flink', 'FLINK']:
                    start_resp = kinesis_analytics_client.start_application(
                        ApplicationName=application_name,
                        RunConfiguration={"ApplicationRestoreConfiguration":
                                          {"ApplicationRestoreType": "SKIP_RESTORE_FROM_SNAPSHOT"}})
                else:
                    raise KeyError('At present moment Kinesis analytics application can be sql or flink only')
                if start_resp['ResponseMetadata']['HTTPStatusCode'] == 200:
                    _wait_for_status(
                        kinesis_analytics_client, application_name, 'RUNNING', wait_to_start, sleep_interval)
                    return
                else:
                    time.sleep(2 * sleep_interval)
            except ClientError as ee:
                raise ee
        raise RuntimeError(f'Can not start application {application_name}')
    else:
        if no_more_retries:
            raise RuntimeError(f'Application {application_name} is not in READY or RUNNING state. '
                               'No more attempts to wait for above-mentioned statuses.')
        else:
            # interval_status_change = 24 * sleep_interval
            logging.info(f'Application {application_name} is not in READY or RUNNING state. '
                         f'Wait for {str(wait_to_start)} seconds and try again.')
            time.sleep(wait_to_start)
            start_kinesis_analytics_app(application_name, input_id, app_type, session, no_more_retries=True)
    return


def stop_kinesis_analytics_app(app_name: str, session: Session,
                               sleep_interval=ORDINARY_SLEEP_INTERVAL):
    """
    stops or force-stops kinesis analytics application
    """
    kinesis_analytics_client = client('kinesisanalyticsv2', session)
    app_status = kinesis_analytics_client.describe_application(
        ApplicationName=app_name)['ApplicationDetail']['ApplicationStatus']
    if app_status == 'RUNNING':
        for _ in range(3):
            kinesis_analytics_client.stop_application(ApplicationName=app_name)
            app_status = kinesis_analytics_client.describe_application(
                ApplicationName=app_name)['ApplicationDetail']['ApplicationStatus']
            print(app_status)
            if app_status == 'STOPPING':
                return
            else:
                time.sleep(sleep_interval)
        for _ in range(3):
            kinesis_analytics_client.stop_application(ApplicationName=app_name,
                                                      Force=True)
            app_status = kinesis_analytics_client.describe_application(
                ApplicationName=app_name)['ApplicationDetail']['ApplicationStatus']
            if app_status == 'STOPPING':
                return
            else:
                time.sleep(sleep_interval)
        logging.warning(f"Kinesis analytics application {app_name} can not be stopped via api, \
            force stop do not help - must stop application manually")
    else:
        logging.warning(f"Kinesis analytics application {app_name} is not RUNNING")
    return


def cache_kinan_app_snapshpots_list(app_name: str, session: Session,
                                    snapshots_retrieve_limit: int = SNAPSHOTS_QUOTA):
    """
    get list of existing kinesis analytics application snapshots
    """
    kinesis_analytics_client = client('kinesisanalyticsv2', session)
    temp_snaps_list = kinesis_analytics_client.list_application_snapshots(
        ApplicationName=app_name,
        Limit=snapshots_retrieve_limit)['SnapshotSummaries']
    return [tt['SnapshotName'] for tt in temp_snaps_list]


def _snapshot_postfix(postfix_digits=6):
    """
    return postfix_digits length random string for naming purpose
    """
    return ''.join(choices(string.ascii_lowercase + string.digits, k=postfix_digits))


def _new_test_standard_snapshot_name(app_name):
    """
    if new snapshot name was not provided, construct as in this foo.
    this foo may be easily overwritten in tail of snapshot name,
    but:
        - do NOT overwrite "TEST" commence of standard snapshot name
    """
    return "TEST-" + app_name + '-' + _snapshot_postfix()


def provide_test_snapshot_name(app_name, input_snapshot_name):
    """
    returns new snapshot name, which is:
        - standard snapshot name if input_snapshot_name is None
        - or test snapshot name if 'construct_test_snapshot_name'
        - input_snapshot_name otherwise
    """
    return input_snapshot_name if input_snapshot_name is not None \
        and input_snapshot_name != STANDARD_SNAPSHOT_NAME_MARK \
        else _new_test_standard_snapshot_name(app_name)


def extract_running_app_snapshot_name(app_name: str, session: Session):
    """
    for running application extract snapshot name, if any.
    """
    kinesis_analytics_client = client('kinesisanalyticsv2', session)
    app_run_configuration = kinesis_analytics_client.describe_application(
        ApplicationName=app_name,
        IncludeAdditionalDetails=True
    )['ApplicationDetail']['ApplicationConfigurationDescription']['RunConfigurationDescription']
    app_run_configuration = app_run_configuration['ApplicationRestoreConfigurationDescription']
    return app_run_configuration.get('SnapshotName')


def provide_latest_snapshot(app_name: str, session: Session):
    """
    returns name of the latest snapshot
    """
    return cache_kinan_app_snapshpots_list(app_name,
                                           session)[-1]


def extract_running_app_status_code(app_name: str, session: Session):
    """
    returns kinesis data analytics application status_code
    """
    kinesis_analytics_client = client('kinesisanalyticsv2', session)
    app_metadata = kinesis_analytics_client.describe_application(
        ApplicationName=app_name,
        IncludeAdditionalDetails=True
    )['ResponseMetadata']
    return str(app_metadata['HTTPStatusCode'])


def extract_restore_type(app_name: str, session: Session):
    """
    returns kinesis data analytics restore type
    """
    kinesis_analytics_client = client('kinesisanalyticsv2', session)
    restore_type = kinesis_analytics_client.describe_application(
        ApplicationName=app_name,
        IncludeAdditionalDetails=True
    )['ApplicationDetail']['ApplicationConfigurationDescription']['RunConfigurationDescription']
    restore_type = restore_type['ApplicationRestoreConfigurationDescription']
    restore_type = restore_type['ApplicationRestoreType']
    return restore_type


def prove_snapshot_exist_or_confect(app_name: str, snapshot_name: str, session: Session):
    """
    if snapshot with name "snapshot_name" exist, pass and return "False" for teardown
    if snapshot_name is "Latest", or snapshot with "snapshot_name" does NOT exist,
    confect new snapshot and return True and new snapshot name for teardown
    """
    existent_snapshots_names = cache_kinan_app_snapshpots_list(app_name, session)
    if snapshot_name in existent_snapshots_names:
        logging.info(f'Kinesis data analytics application {app_name} already has snapshot '
                     f'with name: {snapshot_name}. This name will be used for recover.')
        return False, None
    elif snapshot_name in ['Latest', 'latest']:
        if len(existent_snapshots_names) == 0:
            confect_snapshot_name = _new_test_standard_snapshot_name(app_name)
            logging.info(f'Kinesis data analytics application {app_name} '
                         'does not have snapshots. New snapshot with name '
                         f'{confect_snapshot_name} will be confected and used for recover.')
        else:
            existent_latest_snapshot_name = existent_snapshots_names[-1]
            logging.info(f'Kinesis data analytics application {app_name} '
                         'already has latest snapshot with name '
                         f'{existent_latest_snapshot_name}. This name '
                         'will be used for recover.')
            return False, None
    else:
        confect_snapshot_name = snapshot_name
        logging.info(f'Kinesis data analytics application {app_name} '
                     f'does not have snapshot with name {confect_snapshot_name}. '
                     f'New snapshot with provided name {confect_snapshot_name} '
                     f'will be confected and used for recover.')
        kinesis_analytics_client = client('kinesisanalyticsv2', session)
        kinesis_analytics_client.create_application_snapshot(
            ApplicationName=app_name,
            SnapshotName=confect_snapshot_name)['ResponseMetadata']['HTTPStatusCode']
        logging.info(f'New snapshot with name {confect_snapshot_name} for application '
                     f'{app_name} successfully confected.')
    return True, confect_snapshot_name


def add_kda_application_to_vpc(app_name, vpc_id, subnet_id, security_groups_id_list, session):
    """
    Add Kinesis Data Analytics application to VPC
    return True or False for add-to-vpc teardown
    """
    kinesis_analytics_client = client('kinesisanalyticsv2', session)
    conditional_token = obtain_conditional_token(
        {'ApplicationName': app_name}, {}, kinesis_analytics_client)
    security_groups_ids_list = security_groups_id_list.split(',')
    try:
        subnet_status = kinesis_analytics_client.describe_application(
            ApplicationName=app_name,
            IncludeAdditionalDetails=True)['ApplicationDetail']['ApplicationConfigurationDescription']
        already_vpc_id = subnet_status['VpcConfigurationDescriptions'][0]['VpcId']
        vpc_configuration_id = subnet_status['VpcConfigurationDescriptions'][0]['VpcConfigurationId']
        if already_vpc_id == vpc_id:
            logging.info(f'Kinesis Data Analytics application {app_name} '
                         f'is already added to provided VPC {vpc_id}. Skip VPC add.')
            return 'No', None
        else:
            logging.error(f'For this test Kinesis Data Analytics application {app_name} '
                          f'must be in the VPC {vpc_id} with Kinesis streams endpoint. '
                          f'Abort now.')
            raise
    except Exception:
        logging.info(f'Now start add Kinesis Data Analytics application {app_name} to VPC {vpc_id}.')
    kinesis_analytics_client.add_application_vpc_configuration(
        ApplicationName=app_name,
        ConditionalToken=conditional_token,
        VpcConfiguration={
            'SubnetIds': [subnet_id],
            'SecurityGroupIds': security_groups_ids_list})['ResponseMetadata']['HTTPStatusCode']
    logging.info(f'Kinesis Data Analytics application {app_name} included to VPC {vpc_id} '
                 f'with Subnet ID {subnet_id} and Security group ID [{security_groups_id_list}]')
    _wait_for_status(
        kinesis_analytics_client, app_name, "RUNNING")
    subnet_status = kinesis_analytics_client.describe_application(
        ApplicationName=app_name,
        IncludeAdditionalDetails=True)['ApplicationDetail']['ApplicationConfigurationDescription']
    vpc_configuration_id = subnet_status['VpcConfigurationDescriptions'][0]['VpcConfigurationId']
    return 'Yes', vpc_configuration_id


def get_kda_vpc_security_groups_id_list(app_name: str, session: Session) -> list:
    """
    Get Kinesis Data Analytics VPC security group ids
    """
    kinesis_analytics_client = client('kinesisanalyticsv2', session)
    security_groups_id_list = get_kda_vpc_security_group(
        {'ApplicationName': app_name}, {}, kinesis_analytics_client)
    return security_groups_id_list["KinesisDataAnalyticsApplicationVPCSecurityGroupMappingOriginalValue"]


def trigger_input_stream_lambda_loader_several_times(lambda_loader_name: str,
                                                     invoke_attempts: int,
                                                     session: Session):
    """
    triggers input stream lambda loader several times, to put dummy ticker data to input stream
    """
    lambda_client = client('lambda', session)
    i = 0
    while i < invoke_attempts:
        lambda_client.invoke(
            FunctionName=lambda_loader_name
        )
        i += 1
    return
