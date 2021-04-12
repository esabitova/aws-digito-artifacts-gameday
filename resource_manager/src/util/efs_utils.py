import boto3
import logging

efs_client = boto3.client('efs')
LOG = logging.getLogger(__name__)


def describe_filesystem(fs_id: str):
    """
    Describe filesystem by efs ID
    :param fs_id ID of the file system whose description you want to retrieve
    """

    response = efs_client.describe_file_systems(FileSystemId=fs_id)

    return response
