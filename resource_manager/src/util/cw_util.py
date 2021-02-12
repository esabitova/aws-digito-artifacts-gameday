import boto3
import logging


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

    cw = session.client('cloudwatch')
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


