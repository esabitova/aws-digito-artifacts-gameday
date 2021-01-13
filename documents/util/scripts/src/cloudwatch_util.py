import boto3
import time
from datetime import datetime, timedelta


def get_ec2_metric_max_datapoint(instance_id, metric_name, start_time_utc, end_time_utc):
    """
    Returns metric data point witch represents highest data point value for given metric name and EC2 instance id.
    :param instance_id: The EC2 instance id
    :param metric_name: The metric name
    :param start_time_utc: The metric interval start time in UTC
    :param end_time_utc: The metric interval end time in UTC
    :return: The highest data point value.
    """
    cw = boto3.client('cloudwatch')
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
    max_datapoint = 0.0
    for dp in response['Datapoints']:
        dp_number = float(dp['Maximum'])
        max_datapoint = max_datapoint if max_datapoint > dp_number else dp_number
    return max_datapoint


def describe_metric_alarm_state(alarm_name):
    """
    Returns alarm state for given alarm name.
    :param alarm_name: The alarm name
    :return: The alarm state.
    """
    cw = boto3.client('cloudwatch')
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
