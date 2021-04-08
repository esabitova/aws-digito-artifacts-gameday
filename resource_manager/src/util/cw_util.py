import boto3
import logging
import time
from resource_manager.src import constants
from .boto3_client_factory import client


def get_ec2_metric_max_datapoint(session: boto3.Session, start_time_utc, end_time_utc, metric_namespace: str,
                                 metric_name: str, metric_dimensions: {}, period: int):
    """
    Returns metric data point witch represents highest data point value for given metric name and EC2 instance id:
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudwatch.html#CloudWatch.Client.get_metric_statistics
    :param session The boto3 session
    :param metric_namespace: The metric namespace
    :param metric_name: The metric name
    :param start_time_utc: The metric interval start time in UTC
    :param end_time_utc: The metric interval end time in UTC
    :param metric_dimensions The dictionary of metric dimensions
    :param period The metric period
    :return: The highest data point value.
    """
    dimensions = []
    for key, value in metric_dimensions.items():
        dimensions.append({"Name": key, "Value": value})

    cw = client('cloudwatch', session)
    response = cw.get_metric_statistics(
        Namespace=metric_namespace,
        MetricName=metric_name,
        Dimensions=dimensions,
        StartTime=start_time_utc,
        EndTime=end_time_utc,
        Period=period,
        Statistics=["Maximum"],
        Unit='Percent'
    )

    data_points = response['Datapoints']
    logging.info("[{}] metric for interval [{}::{}] data points: {}".format(metric_name, str(start_time_utc),
                                                                            str(end_time_utc), data_points))
    max_dp = 0.0
    for dp in data_points:
        if max_dp < float(dp['Maximum']):
            max_dp = float(dp['Maximum'])
    return max_dp


def get_metric_alarm_state(session: boto3.Session, alarm_name: str):
    """
    Returns metric alarm state by its name
    :param session: The boto3 session
    :param alarm_name: The metric alarm name
    :return: The metric alarm state
    """
    cw = client('cloudwatch', session)
    logging.info(f"Fetching status for alarm {alarm_name}")
    response = cw.describe_alarms(AlarmNames=[alarm_name])
    if not response or 'MetricAlarms' not in response or len(response['MetricAlarms']) == 0:
        raise Exception(f"Alarm {alarm_name} not found")
    return response['MetricAlarms'][0]['StateValue']


def wait_for_metric_alarm_state(session: boto3.Session, alarm_name: str, expected_alarm_state: str, time_to_wait: int):
    """
    Waits for alarm to be in expected step for time_to_wait seconds and returns
    :param session The boto3 session
    :param alarm_name: The metric alarm name
    :param expected_alarm_state: The expected status to wait for
    :param time_to_wait: Max time in seconds to wait
    :return: True if step achieved, raise Exception otherwise
    """
    start_time = time.time()
    elapsed_time = time.time() - start_time
    alarm_state = get_metric_alarm_state(session, alarm_name)

    # Wait for execution step to resolve in waiting or one of terminating statuses
    while alarm_state != expected_alarm_state:
        if elapsed_time > time_to_wait:
            raise Exception(f'Waiting for alarm {alarm_name} to be in step {expected_alarm_state} timed out')
        time.sleep(constants.sleep_time_secs)
        alarm_state = get_metric_alarm_state(session, alarm_name)
        elapsed_time = time.time() - start_time
    return True
