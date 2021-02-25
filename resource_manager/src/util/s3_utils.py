from typing import List

import boto3

s3_client = boto3.client('s3')


def put_object(bucket_name: str, key: str, body: bytes):
    """
    Put object to S3 bucket
    :param bucket_name: bucket name
    :param key: object key
    :param body: content of the object
    """
    s3_client.put_object(Bucket=bucket_name, Key=key, Body=body)


def clean_bucket(bucket_name: str):
    """
    Clean the bucket
    :param bucket_name: the bucket name
    """

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


def get_number_of_files(bucket_name) -> int:
    """
    Get number of files in the bucket
    :param bucket_name: bucket name
    :return: number of files in the bucket
    """
    contents = __list_objects(bucket_name).get('Contents')
    return 0 if not contents else len(contents)


def __list_objects(bucket_name):
    """
    Get the list of the objects in the bucket without version checking and delete markers
    :param bucket_name: bucket name
    :return: list of the objects in the bucket
    """
    return s3_client.list_objects_v2(Bucket=bucket_name)
