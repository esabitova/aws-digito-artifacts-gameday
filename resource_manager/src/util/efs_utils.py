import boto3
import logging
from .boto3_client_factory import client
logger = logging.getLogger(__name__)


def describe_filesystem(session: boto3.Session, fs_id: str, region: str = None):
    """
    Describe filesystem by efs ID
    :param session boto3 client session
    :param fs_id ID of the file system whose description you want to retrieve
    :param region Name of region to look for fs, if None, use current region
    """
    if region:
        efs_client = session.client('efs', region_name=region)
    else:
        efs_client = client('efs', session)
    response = efs_client.describe_file_systems(FileSystemId=fs_id)

    return response


def delete_filesystem(session: boto3.Session, fs_id: str, region: str = None):
    """
    Delete filesystem by efs ID
    :param session boto3 client session
    :param fs_id ID of the file system whose description you want to retrieve
    :param region Name of region to look for fs, if None, use current region
    """
    if region:
        efs_client = session.client('efs', region_name=region)
    else:
        efs_client = client('efs', session)
    efs_client.delete_file_system(FileSystemId=fs_id)
