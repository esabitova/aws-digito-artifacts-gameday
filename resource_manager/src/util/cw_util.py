import boto3
import logging


def get_ec2_metric_max_datapoint(session: boto3.Session, instance_id, metric_name, start_time_utc, end_time_utc):
    """
    Returns metric data point witch represents highest data point value for given metric name and EC2 instance id.
    :param instance_id: The EC2 instance id
    :param metric_name: The metric name
    :param start_time_utc: The metric interval start time in UTC
    :param end_time_utc: The metric interval end time in UTC
    :return: The highest data point value.
    """
    cw = session.client('cloudwatch')
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