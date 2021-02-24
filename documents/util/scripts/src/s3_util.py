import boto3
from datetime import datetime

s3_client = boto3.client('s3')


def check_existence_of_objects_in_bucket(events, context):
    """
    Check existence of versioned and deleted objects in bucket
    :return: Number of objects exist in restore bucket
    """
    if 'S3BucketToRestoreName' not in events:
        raise KeyError('Requires S3BucketToRestoreName  in events')

    s3_bucket_to_restore_name = events['S3BucketToRestoreName']

    print(f'Sending the list_object_versions request fore the {s3_bucket_to_restore_name} bucket...')
    response: dict = s3_client.list_object_versions(Bucket=s3_bucket_to_restore_name)
    print(f'The response from the list_object_versions: {response}')

    versions: dict = response.get('Versions')
    delete_markers: dict = response.get('DeleteMarkers')

    number_of_objects_exist_in_restore_bucket = 0
    if versions:
        number_of_objects_exist_in_restore_bucket += len(versions)
    if delete_markers:
        number_of_objects_exist_in_restore_bucket += len(delete_markers)

    print(f'The number of existing objects in restore bucket is {number_of_objects_exist_in_restore_bucket}')

    return {'NumberOfObjectsExistInRestoreBucket': str(number_of_objects_exist_in_restore_bucket),
            "AreObjectsExistInRestoreBucket": False if number_of_objects_exist_in_restore_bucket == 0 else True}


def clean_bucket(events, context):
    """
    Clean bucket by removing versioned objects and delete markers
    :return: Number of removed versioned objects and delete markers
    """
    if 'S3BucketToRestoreName' not in events:
        raise KeyError('Requires S3BucketToRestoreName  in events')

    s3_bucket_to_restore_name = events['S3BucketToRestoreName']

    print(f'Sending the list_object_versions request fore the {s3_bucket_to_restore_name} bucket...')

    paginator = s3_client.get_paginator('list_object_versions')
    pages = paginator.paginate(Bucket=s3_bucket_to_restore_name)

    for page in pages:
        print(f'The response from the list_object_versions: {page}')

        number_of_deleted_objects = 0

        versions: dict = page.get('Versions')
        for version in versions:
            key = version.get('Key')
            version_id = version.get('VersionId')

            s3_client.delete_object(Bucket=s3_bucket_to_restore_name, Key=key, VersionId=version_id)

            print(f'The versioned object with Bucket={s3_bucket_to_restore_name}, '
                  f'Key={key}, VersionId={version_id} was deleted')

            number_of_deleted_objects += 1

        delete_markers: dict = page.get('DeleteMarkers')
        for delete_marker in delete_markers:
            key = delete_marker.get('Key')
            version_id = delete_marker.get('VersionId')

            s3_client.delete_object(Bucket=s3_bucket_to_restore_name, Key=key, VersionId=version_id)

            print(f'The delete marker with Bucket={s3_bucket_to_restore_name},'
                  f' Key={key}, VersionId={version_id} was deleted')

            number_of_deleted_objects += 1

    print(f'The number of deleted versioned objects and delete markers '
          f'in restore bucket is {number_of_deleted_objects}')

    return {'NumberOfDeletedObjects': number_of_deleted_objects}


def restore_from_backup(events, context):
    """
    Restore objects from backup bucket
    :return: Copied files number, recovery time seconds
    """
    if 'S3BucketToRestoreName' not in events or 'S3BackupBucketName' not in events:
        raise KeyError('Requires S3BucketToRestoreName or S3BackupBucketName  in events')

    start = datetime.now()

    s3_backup_bucket_name = events['S3BackupBucketName']
    s3_bucket_to_restore_name = events['S3BucketToRestoreName']

    paginator = s3_client.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=s3_backup_bucket_name)

    print(f'Starting to copy files from the {s3_backup_bucket_name} bucket '
          f'to the {s3_bucket_to_restore_name} bucket...')

    copied_count = 0
    for page in pages:
        print(f'The response from the list_objects_v2: {page}')
        for content in page["Contents"]:
            print(f'Copying the file {content["Key"]}...')

            copy_source = {
                'Bucket': s3_backup_bucket_name,
                'Key': content["Key"]
            }
            s3_client.copy(copy_source, s3_bucket_to_restore_name, content["Key"])

            print(f'The file {content["Key"]} was successfully copied')

            copied_count += 1

    print(f'The file number of copied files is {copied_count}')

    return {'CopiedFilesNumber': copied_count, 'RecoveryTimeSeconds': int((datetime.now() - start).total_seconds())}
