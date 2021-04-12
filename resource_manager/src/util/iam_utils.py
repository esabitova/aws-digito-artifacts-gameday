import boto3
import logging

iam_client = boto3.client('iam')
LOG = logging.getLogger(__name__)


def get_role_by_name(role_name: str):
    """
    Describe role by name
    :param role_name The name of the IAM role to get information about. Accepts wildcard
    """
    response = iam_client.get_role(
        RoleName=role_name
    )

    return response
