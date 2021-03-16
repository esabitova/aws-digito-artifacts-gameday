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
    pages = __list_objects(bucket_name)

    contents_counter = 0
    for page in pages:
        contents = page.get('Contents')
        contents_counter += 0 if not contents else len(contents)

    return contents_counter


def __list_objects(bucket_name) -> List[dict]:
    """
    Get the paginated list of the objects in the bucket without version checking and delete markers
    :param bucket_name: bucket name
    :return: list of the objects in the bucket
    """
    paginator = s3_client.get_paginator('list_objects_v2')
    return paginator.paginate(Bucket=bucket_name)


def get_versions(bucket_name: str, object_key: str, max_keys=1000) -> List:
    """
    Get versions of the object from the bucket
    :param max_keys: maximum number of keys returned in the response
    :param bucket_name: the bucket name
    :param object_key:  the name of the object
    :return: versions of the object from the bucket
    """

    paginator = s3_client.get_paginator('list_object_versions')
    pages = paginator.paginate(Bucket=bucket_name, Prefix=object_key, MaxKeys=max_keys)
    versions: List = []
    for page in pages:
        page_versions = page.get('Versions')
        if page_versions is not None:
            versions.extend(page_versions)
    return versions


def get_object(s3_bucket_name, object_key, version_id) -> dict:
    """
    Get the object
    :param s3_bucket_name: bucket name
    :param object_key: object key
    :param version_id: version id
    :return: the object
    """
    return s3_client.get_object(Bucket=s3_bucket_name, Key=object_key, VersionId=version_id)
