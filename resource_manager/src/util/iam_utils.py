from boto3 import Session
import logging
from .boto3_client_factory import client
LOG = logging.getLogger(__name__)


def get_role_by_name(session: Session, role_name: str):
    """
    Describe role by name
    :param session boto3 client session
    :param role_name The name of the IAM role to get information about. Accepts wildcard
    """
    iam_client = client('iam', session)

    response = iam_client.get_role(
        RoleName=role_name
    )

    return response
