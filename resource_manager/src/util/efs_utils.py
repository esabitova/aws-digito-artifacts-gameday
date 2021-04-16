from boto3 import Session
import logging
from .boto3_client_factory import client
logger = logging.getLogger(__name__)


def describe_filesystem(session: Session, fs_id: str):
    """
    Describe filesystem by efs ID
    :param session boto3 client session
    :param fs_id ID of the file system whose description you want to retrieve
    """
    efs_client = client('efs', session)
    response = efs_client.describe_file_systems(FileSystemId=fs_id)

    return response
