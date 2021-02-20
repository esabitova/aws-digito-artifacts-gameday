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
    files = __list_objects(bucket_name).get('Contents')
    if files:
        keys: List = []
        for file in files:
            keys.append({'Key': file['Key']})
        s3_client.delete_objects(Bucket=bucket_name, Delete={'Objects': keys})


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
    Get the list of the objects in the bucket
    :param bucket_name: bucket name
    :return: list of the objects in the bucket
    """
    return s3_client.list_objects_v2(Bucket=bucket_name)
