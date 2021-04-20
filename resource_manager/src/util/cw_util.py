import logging
import time
from resource_manager.src.util.enums.alarm_type import AlarmType
from resource_manager.src.util.enums.alarm_state import AlarmState
from boto3 import Session
from .boto3_client_factory import client
from resource_manager.src import constants
from .enums.operator import Operator


def __get_alarms_state(session: Session, alarm_name: str, alarm_type: AlarmType) -> AlarmState:
    """
    Returns the current state of the given alarm by calling
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudwatch.html#CloudWatch.Client.describe_alarms
    :param session: The boto3 session
    :param alarm_name: The alarm name
    :param alarm_type: The type of alarm (COMPOSITE or METRIC)
    :return: The one of the following values 'OK'|'ALARM'|'INSUFFICIENT_DATA'
    """
    cw = client('cloudwatch', session)

    alarm_type_switcher = {
        AlarmType.COMPOSITE: "CompositeAlarms",
        AlarmType.METRIC: "MetricAlarms"
    }

    alarm_description = cw.describe_alarms(AlarmNames=[alarm_name])
    if not alarm_description['ResponseMetadata']['HTTPStatusCode'] == 200:
        logging.error(alarm_description)
        raise ValueError('Failed to describe alarms')
    print(alarm_description)

    alarm_descriptions = alarm_description[alarm_type_switcher[alarm_type]]
    if len(alarm_descriptions) > 0:
        return AlarmState[alarm_description[alarm_type_switcher[alarm_type]][0]['StateValue']]
    else:
        raise ValueError(f'Given alarm ({alarm_name}) was not found')


def get_cw_metric_statistics(session: Session, start_time_utc, end_time_utc, metric_namespace: str,
                             metric_name: str, metric_dimensions: {}, period: int, statistics: str, unit: str = None):
    cw = client('cloudwatch', session)

    request = {
        "Namespace": metric_namespace,
        "MetricName": metric_name,
        "Dimensions": [
            {"Name": key, "Value": value}
            for key, value in metric_dimensions.items()],
        "StartTime": start_time_utc,
        "EndTime": end_time_utc,
        "Period": period,
        "Statistics": statistics,
    }
    if unit:
        request["Unit"] = unit

    response = cw.get_metric_statistics(**request)
    return response["Datapoints"]


def get_ec2_metric_max_datapoint(session: Session, start_time_utc, end_time_utc, metric_namespace: str,
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
    data_points = get_cw_metric_statistics(session, start_time_utc, end_time_utc,
                                           metric_namespace, metric_name,
                                           metric_dimensions, period, ["Maximum"],
                                           "Percent")
    logging.info("[{}] metric for interval [{}::{}] data points: {}".format(metric_name, str(start_time_utc),
                                                                            str(end_time_utc), data_points))
    max_dp = 0.0
    for dp in data_points:
        if max_dp < float(dp['Maximum']):
            max_dp = float(dp['Maximum'])
    return max_dp


def wait_for_metric_data_point(session: Session, name: str, datapoint_threshold: float,
                               operator: Operator, start_time_utc, end_time_utc, namespace, dimensions: [] = [],
                               period: int = 60, time_out_secs: int = 600, sleep_time_sec: int = 20,
                               unit: str = 'Percent', statistics: [] = ["Maximum"]) -> float:
    """
    Waits for metric data point based on given operator and datapoint.
    Times out if metric is not find after waiting for 'time_out_secs' duration.
    :param session: The boto3 session
    :param name: The metric name
    :param datapoint_threshold: The expected metric data point
    :param operator: The expected metric comparison operator
    :param start_time_utc: The metric data points start time
    :param end_time_utc: The metric data points end time
    :param namespace: The metric namespace
    :param dimensions: The metric dimensions
    :param period: The metric period (default: 60 seconds)
    :param time_out_secs: The waiting time out in seconds (default: 600 seconds)
    :param sleep_time_sec: The sleep time between waiting iterations (default: 20 seconds)
    :param unit: The metric unit (default: Percent)
    :param statistics: The metric statistics (default: ['Maximum'])
    :return: The desired metric data point
    """
    elapsed_time_secs = 0
    while elapsed_time_secs < time_out_secs:
        data_points = get_cw_metric_statistics(session, start_time_utc, end_time_utc,
                                               namespace, name, dimensions, period, statistics, unit)
        logging.info("[{}] metric for interval [{}::{}] data points: {}".format(name, str(start_time_utc),
                                                                                str(end_time_utc), data_points))

        for dp in data_points:
            dp_max = float(dp['Maximum'])
            if operator == Operator.MORE_OR_EQUAL and dp_max >= datapoint_threshold:
                return dp_max
            elif operator == Operator.LESS_OR_EQUAL and dp_max <= datapoint_threshold:
                return dp_max

        logging.info(f'Waiting for [{name}] metric data point to be [{operator}] to [{datapoint_threshold}] {unit}')
        time.sleep(sleep_time_sec)
        elapsed_time_secs = elapsed_time_secs + sleep_time_sec
    raise Exception(f'Waiting for [{name}] metric data point to be [{operator} {datapoint_threshold}] '
                    f'timed out after [{time_out_secs}] seconds.')


def wait_for_metric_alarm_state(session: Session, alarm_name: str, expected_alarm_state: str, time_to_wait: int):
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
    while alarm_state.name != expected_alarm_state:
        if elapsed_time > time_to_wait:
            raise Exception(f'Waiting for alarm {alarm_name} to be in step {expected_alarm_state} timed out')
        time.sleep(constants.sleep_time_secs)
        alarm_state = get_metric_alarm_state(session, alarm_name)
        elapsed_time = time.time() - start_time
    return True


def get_metric_alarm_state(session: Session, alarm_name: str) -> AlarmState:
    """
    Returns the current state of the given alarm by calling
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudwatch.html#CloudWatch.Client.describe_alarms
    Use another function to get value of composite alarm
    :param session: The boto3 session
    :param alarm_name: The alarm name
    :return: The one of the following values 'OK'|'ALARM'|'INSUFFICIENT_DATA'
    """
    return __get_alarms_state(session=session,
                              alarm_name=alarm_name,
                              alarm_type=AlarmType.METRIC)
