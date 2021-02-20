import boto3

iam_client = boto3.client('iam')


def get_current_user_arn():
    """
    Get current IAM user ARN
    :return: current IAM user ARN
    """
    user: dict = iam_client.get_user()
    return user['User']['Arn']
