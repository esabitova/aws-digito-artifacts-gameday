import logging
import time
from datetime import datetime, timedelta
from typing import Any, Callable

import boto3
from botocore.config import Config

PUT_METRIC_ALARM_PARAMS = ['AlarmName', 'AlarmDescription', 'ActionsEnabled', 'OKActions',
                           'AlarmActions', 'InsufficientDataActions', 'MetricName', 'Namespace', 'Statistic',
                           'ExtendedStatistic',
                           'Dimensions', 'Period', 'Unit', 'EvaluationPeriods', 'DatapointsToAlarm',
                           'Threshold', 'ComparisonOperator', 'TreatMissingData', 'EvaluateLowSampleCountPercentile',
                           'Metrics', 'Tags', 'ThresholdMetricId']


def _execute_boto3_cloudwatch(delegate: Callable[[Any], dict]) -> dict:
    cloudwatch_client = boto3.client('cloudwatch')
    response = delegate(cloudwatch_client)
    if not response['ResponseMetadata']['HTTPStatusCode'] == 200:
        logging.error(response)
        raise ValueError('Failed to execute request')
    return response


def _describe_metric_alarms():
    """
    Returns all alarms setup in the current region
    """
    return _execute_boto3_cloudwatch(
        delegate=lambda x: x.describe_alarms(AlarmTypes=['MetricAlarm']))


def _put_metric_alarm(**kwargs):
    """
    Updates or creates metric alarm with the given paramters:
    :param kwargs: The parametes for boto3 put_metric_alarm
    """
    return _execute_boto3_cloudwatch(
        delegate=lambda x: x.put_metric_alarm(**kwargs))


def copy_alarms_for_dynamo_db_table(events, context):
    """
    Copies all the given alarm names from the source to the target table
    """
    if 'SourceTableName' not in events:
        raise KeyError('Requires SourceTableName')
    if 'TargetTableName' not in events:
        raise KeyError('Requires TargetTableName')
    if 'DynamoDBSourceTableAlarmNames' not in events:
        raise KeyError('Requires DynamoDBSourceTableAlarmNames')

    source_table_name: str = events['SourceTableName']
    target_table_name: str = events['TargetTableName']
    alarms_names: str = events.get('DynamoDBSourceTableAlarmNames', [])
    logging.info(
        f"Coping alarms for dynamodb table. Source: {source_table_name}, "
        f"Target: {target_table_name}. Alarm Names: {alarms_names}")
    source_alarms = _describe_metric_alarms()
    logging.info(f"Source Table alarms: {source_alarms}")

    alarms_copied_count: int = 0

    for alarm in filter(lambda x: x.get('Namespace', '') == 'AWS/DynamoDB', source_alarms.get('MetricAlarms', [])):
        copy_alarm = False
        for dimension in alarm['Dimensions']:
            if dimension['Name'] == 'TableName' and \
                dimension['Value'] == source_table_name and \
                    any([a for a in alarms_names if a in alarm['AlarmName']]):
                copy_alarm = True
                dimension['Value'] = target_table_name
                alarm['AlarmName'] = f"{alarm['AlarmName']}_{target_table_name}"

        if copy_alarm:
            keys = [*alarm.keys()]
            for key in keys:
                if key not in PUT_METRIC_ALARM_PARAMS:
                    del alarm[key]
            _put_metric_alarm(**alarm)
            alarms_copied_count += 1
            copy_alarm = False

    return {
        "AlarmsChanged": alarms_copied_count
    }


def get_ec2_metric_max_datapoint(instance_id, metric_name, start_time_utc, end_time_utc):
    """
    Returns metric data point witch represents highest data point value for given metric name and EC2 instance id.
    :param instance_id: The EC2 instance id
    :param metric_name: The metric name
    :param start_time_utc: The metric interval start time in UTC
    :param end_time_utc: The metric interval end time in UTC
    :return: The highest data point value.
    """
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    cw = boto3.client('cloudwatch', config=config)
    response = cw.get_metric_statistics(
        Namespace="AWS/EC2",
        MetricName=metric_name,
        Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
        # CPU metric delay is 5 minutes
        StartTime=start_time_utc,
        EndTime=end_time_utc,
        # Minimum period for CPU/Memory metric - 5 minutes
        Period=300,
        Statistics=["Maximum"],
        Unit='Percent'
    )

    data_points = response['Datapoints']
    logging.info("[{}] metric for interval [{}::{}] data points: {}".format(metric_name, str(start_time_utc),
                                                                            str(end_time_utc), data_points))
    latest_datapoint = 0.0
    latest_dp_timestamp = 0
    for dp in data_points:
        current_dp_timestamp = dp['Timestamp'].timestamp()
        if latest_dp_timestamp < current_dp_timestamp:
            latest_dp_timestamp = current_dp_timestamp
            latest_datapoint = float(dp['Maximum'])
    return latest_datapoint


def describe_metric_alarm_state(alarm_name):
    """
    Returns alarm state for given alarm name.
    :param alarm_name: The alarm name
    :return: The alarm state.
    """
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    cw = boto3.client('cloudwatch', config=config)
    response = cw.describe_alarms(
        AlarmNames=[alarm_name],
        AlarmTypes=[
            'MetricAlarm'
        ]
    )
    metric_alarms = response.get('MetricAlarms')
    if not metric_alarms:
        raise Exception("MetricAlarm [{}] does not exist.".format(alarm_name))
    return metric_alarms[0]['StateValue']


def verify_cpu_stress(events, context):
    """
    Verify CPU stress for given instances.
    :param events: The object which contains passed parameters from SSM document
    :param context: The context object for SSM documnent.
    """
    if 'InstanceIds' not in events\
            or 'StressDuration' not in events\
            or 'StressPercentage' not in events\
            or 'ExpectedRecoveryTime' not in events:
        raise KeyError('Requires InstanceIds, StressDuration, StressPercentage, ExpectedRecoveryTime in events')

    instance_ids = events['InstanceIds']
    exp_load_percentage = float(events['StressPercentage'])
    stress_duration = int(events['StressDuration'])
    exp_recovery_time = int(events['ExpectedRecoveryTime'])

    verify_ec2_stress(instance_ids, stress_duration, exp_load_percentage, 360, 'CPUUtilization', exp_recovery_time)


def verify_memory_stress(events, context):
    """
    Monitors Memory stress behaviour for given instances.
    :param events: The object which contains passed parameters from SSM document
    :param context: The context object for SSM documnent.
    """
    if 'InstanceIds' not in events \
            or 'StressDuration' not in events \
            or 'StressPercentage' not in events \
            or 'ExpectedRecoveryTime' not in events:
        raise KeyError('Requires InstanceIds, StressDuration, StressPercentage, ExpectedRecoveryTime in events')

    raise Exception('Not implemented: https://issues.amazon.com/issues/Digito-1279')


def verify_alarm_triggered(events, context):
    """
    Verify if alarm triggered
    """
    if 'AlarmName' not in events or ('DurationInMinutes' not in events and 'DurationInSeconds' not in events):
        raise KeyError('Requires AlarmName and either DurationInMinutes or DurationInSeconds in events')

    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    cw = boto3.client('cloudwatch', config=config)

    if 'DurationInMinutes' in events:
        start_date = datetime.now() - timedelta(minutes=int(events['DurationInMinutes']))
    else:
        start_date = datetime.now() - timedelta(seconds=int(events['DurationInSeconds']))

    response = cw.describe_alarm_history(
        AlarmName=events['AlarmName'],
        HistoryItemType='StateUpdate',
        MaxRecords=2,
        ScanBy='TimestampDescending',
        StartDate=start_date)

    for alarm_history_item in response['AlarmHistoryItems']:
        if alarm_history_item['HistorySummary'] == "Alarm updated from OK to ALARM":
            return

    raise Exception('Alarm was not triggered')


def verify_ec2_stress(instance_ids, stress_duration, exp_load_percentage, metric_delay, metric_name,
                      exp_recovery_time):
    """
    Helper to verify stress test execution based on metric (CPU/Memory Utilization). Metric indicates whether stress
    testing was performed to specified load level, if not test is failed.
    :param instance_ids: The list of EC2 instance Ids to monitor
    :param stress_duration: The duration of stress test
    :param exp_load_percentage: The CPU/Memory percentage load for stress
    :param metric_delay: The CPU/Memory load metric delay in seconds to be used verify if stress is happening
    :param metric_name: The CPU/Memory load metric name in seconds to be used verify if stress is happening
    :param exp_recovery_time: The expected application recovery time in seconds after stress test
    """

    # Delta is time which we already spend on performing stress test and waiting for recovery time
    delta = stress_duration + exp_recovery_time
    # Wait for metric available (for CPUUtilization minimum 5 minutes delay)
    metric_wait_time = metric_delay - delta if metric_delay - delta > 0 else 0
    time.sleep(metric_wait_time)

    # Start/End time interval for metric
    end_time_utc = datetime.utcnow()
    start_time_utc = end_time_utc - timedelta(seconds=delta)

    for instance_id in instance_ids:
        actual_cpu_load = get_ec2_metric_max_datapoint(instance_id, metric_name, start_time_utc, end_time_utc)
        if actual_cpu_load < exp_load_percentage:
            raise Exception(
                "Instance [{}] expected [{}] load [{}%] but was [{}%]".format(instance_id, metric_name,
                                                                              exp_load_percentage,
                                                                              actual_cpu_load))


def get_metric_alarm_threshold_values(event, context):
    """
    Get alarm threshold and return values above and below
    """
    alarm_name = event['AlarmName']
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    cw = boto3.client('cloudwatch', config=config)
    response = cw.describe_alarms(
        AlarmNames=[alarm_name],
        AlarmTypes=['MetricAlarm']
    )
    metric_alarms = response.get('MetricAlarms')
    if not metric_alarms:
        raise Exception("MetricAlarm [{}] does not exist.".format(alarm_name))
    threshold = metric_alarms[0]['Threshold']
    if threshold == 0:
        raise Exception("MetricAlarm [{}] has no threshold set.".format(alarm_name))

    value_above_threshold = threshold + 1
    value_below_threshold = threshold - 1

    return {
        'Threshold': int(threshold),
        'ValueAboveThreshold': int(value_above_threshold),
        'ValueBelowThreshold': int(value_below_threshold)
    }
