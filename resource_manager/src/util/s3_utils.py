from typing import List

from boto3 import Session

from .boto3_client_factory import client


def put_object(session: Session, bucket_name: str, key: str, body: bytes):
    """
    Put object to S3 bucket
    :param session The boto3 session
    :param bucket_name: bucket name
    :param key: object key
    :param body: content of the object
    """
    s3_client = client('s3', session)
    s3_client.put_object(Bucket=bucket_name, Key=key, Body=body)


def clean_bucket(session: Session, bucket_name: str):
    """
    Clean the bucket
    :param session The boto3 session
    :param bucket_name: the bucket name
    """
    s3_client = client('s3', session)
    paginator = s3_client.get_paginator('list_object_versions')
    pages = paginator.paginate(Bucket=bucket_name)

    for page in pages:
        print(f'The response from the list_object_versions: {page}')

        versions: dict = page.get('Versions')
        if versions is not None:
            for version in versions:
                key = version.get('Key')
                version_id = version.get('VersionId')

                s3_client.delete_object(Bucket=bucket_name, Key=key, VersionId=version_id)

                print(f'The versioned object with Bucket={bucket_name}, '
                      f'Key={key}, VersionId={version_id} was deleted')

        delete_markers: dict = page.get('DeleteMarkers')
        if delete_markers is not None:
            for delete_marker in delete_markers:
                key = delete_marker.get('Key')
                version_id = delete_marker.get('VersionId')

                s3_client.delete_object(Bucket=bucket_name, Key=key, VersionId=version_id)

                print(f'The delete marker with Bucket={bucket_name},'
                      f' Key={key}, VersionId={version_id} was deleted')


def get_number_of_files(session: Session, bucket_name: str) -> int:
    """
    Get number of files in the bucket
    :param session The boto3 session
    :param bucket_name: bucket name
    :return: number of files in the bucket
    """
    pages = __list_objects(session, bucket_name)
    contents_counter = 0
    for page in pages:
        contents = page.get('Contents')
        contents_counter += 0 if not contents else len(contents)

    return contents_counter


def __list_objects(session: Session, bucket_name: str) -> List[dict]:
    """
    Get the paginated list of the objects in the bucket without version checking and delete markers
    :param session The boto3 session
    :param bucket_name: bucket name
    :return: list of the objects in the bucket
    """
    s3_client = client('s3', session)
    paginator = s3_client.get_paginator('list_objects_v2')
    return paginator.paginate(Bucket=bucket_name)


def get_versions(session: Session, bucket_name: str, object_key: str, max_keys=1000) -> List:
    """
    Get versions of the object from the bucket
    :param session The boto3 session
    :param max_keys: maximum number of keys returned in the response
    :param bucket_name: the bucket name
    :param object_key:  the name of the object
    :return: versions of the object from the bucket
    """
    s3_client = client('s3', session)
    paginator = s3_client.get_paginator('list_object_versions')
    pages = paginator.paginate(Bucket=bucket_name, Prefix=object_key, MaxKeys=max_keys)
    versions: List = []
    for page in pages:
        page_versions = page.get('Versions')
        if page_versions is not None:
            versions.extend(page_versions)
    return versions


def get_object(session: Session, s3_bucket_name: str, object_key, version_id) -> dict:
    """
    Get the object
    :param session The boto3 session
    :param s3_bucket_name: bucket name
    :param object_key: object key
    :param version_id: version id
    :return: the object
    """
    s3_client = client('s3', session)
    return s3_client.get_object(Bucket=s3_bucket_name, Key=object_key, VersionId=version_id)


def get_bucket_replication(boto3_session, s3_bucket_name):
    """
    Returns the replication configuration of a bucket.
    :param boto3_session: The boto3 session
    :param s3_bucket_name: bucket name
    :return: replication configuration of a bucket
    """
    s3_client = client('s3', boto3_session)
    return s3_client.get_bucket_replication(Bucket=s3_bucket_name)
