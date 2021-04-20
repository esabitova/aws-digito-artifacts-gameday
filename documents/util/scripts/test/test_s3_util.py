import time
import unittest
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock, call
from documents.util.scripts.src.s3_util import check_existence_of_objects_in_bucket, clean_bucket,\
    restore_from_backup, restore_to_the_previous_version

S3_BUCKET = 's3-bucket'
S3_EMPTY_BUCKET = 's3-empty-bucket'
S3_OWNER_NAME = 'owner-display-name'
S3_OWNER_ID = 'examplee7a2f25102679df27bb0ae12b3f85be6f290b936c4393484be31bebcc'
S3_FILE_VERSION_ID = 'PHtexPGjH2y.zBgT8LmB7wwLI2mpbz.k'
S3_ETAG = '70ee1738b6b21e2c8a43f3a5ab0eee71'

S3_OBJECT_KEY_NO_VERSIONS = 's3-object-key-no-versions'
S3_OBJECT_WITH_VERSIONS = 's3-object-with-versions'


def get_list_objects_v2_response(page=0):
    return {
        'Contents': [
            {
                'ETag': S3_ETAG,
                'Key': f'test{page}_0.txt',
                'LastModified': datetime.now(),
                'Size': 11,
                'StorageClass': 'STANDARD',
            },
            {
                'ETag': S3_ETAG,
                'Key': f'test{page}_1.txt',
                'LastModified': datetime.now(),
                'Size': 11,
                'StorageClass': 'STANDARD',
            },
        ]
    }


def get_list_versions_response(page=0):
    return {
        'Versions': [
            {
                'ETag': S3_ETAG,
                'IsLatest': True,
                'Key': f'test{page}.txt',
                'LastModified': datetime.now(),
                'Owner': {
                    'DisplayName': S3_OWNER_NAME,
                    'ID': S3_OWNER_ID,
                },
                'Size': 3191,
                'StorageClass': 'STANDARD',
                'VersionId': 'null',
            },
            {
                'ETag': S3_ETAG,
                'IsLatest': False,
                'Key': f'test{page}.txt',
                'LastModified': datetime.now(),
                'Owner': {
                    'DisplayName': S3_OWNER_NAME,
                    'ID': S3_OWNER_ID,
                },
                'Size': 3191,
                'StorageClass': 'STANDARD',
                'VersionId': S3_FILE_VERSION_ID,
            }
        ],
        'DeleteMarkers': [
            {
                'Owner': {
                    'DisplayName': S3_OWNER_NAME,
                    'ID': S3_OWNER_ID
                },
                'Key': f'test_deleted{page}.txt',
                'VersionId': S3_FILE_VERSION_ID,
                'IsLatest': True,
                'LastModified': datetime.now()
            },
        ],
    }


def get_list_versions_not_versioned_response():
    return {
        'Versions': [
            {
                'ETag': S3_ETAG,
                'IsLatest': True,
                'Key': S3_OBJECT_KEY_NO_VERSIONS,
                'LastModified': datetime.now(),
                'Owner': {
                    'DisplayName': S3_OWNER_NAME,
                    'ID': S3_OWNER_ID,
                },
                'Size': 3191,
                'StorageClass': 'STANDARD',
                'VersionId': 'null',
            }
        ]
    }


def list_object_versions_side_effect(Bucket, Prefix='', MaxKeys=None):
    # Imitate some working time
    time.sleep(1)
    if Bucket == S3_EMPTY_BUCKET:
        return {}
    if Prefix == S3_OBJECT_KEY_NO_VERSIONS:
        return {
            'Versions': [
                {
                    'ETag': S3_ETAG,
                    'IsLatest': True,
                    'Key': S3_OBJECT_KEY_NO_VERSIONS,
                    'LastModified': datetime.now(),
                    'Owner': {
                        'DisplayName': S3_OWNER_NAME,
                        'ID': S3_OWNER_ID,
                    },
                    'Size': 3191,
                    'StorageClass': 'STANDARD',
                    'VersionId': 'null',
                }
            ]
        }
    return get_list_versions_response()


def list_object_versions_paginated_side_effect(Bucket, Prefix='', MaxKeys=None):
    if Bucket == S3_EMPTY_BUCKET:
        return [{}]
    if Prefix == S3_OBJECT_KEY_NO_VERSIONS:
        return [get_list_versions_not_versioned_response()]
    return [get_list_versions_response(0), get_list_versions_response(1)]


def list_objects_v2_paginated_side_effect(Bucket):
    # Imitate some working time
    time.sleep(1)
    if Bucket == S3_EMPTY_BUCKET:
        return [{
            'Contents': []
        }]
    return [get_list_objects_v2_response(0), get_list_objects_v2_response(1)]


@pytest.mark.unit_test
class TestS3Util(unittest.TestCase):

    def setUp(self):
        self.patcher = patch('boto3.client')
        self.client = self.patcher.start()
        self.s3_service = MagicMock()
        self.side_effect_map = {
            's3': self.s3_service
        }
        self.client.side_effect = lambda service_name, config=None: self.side_effect_map.get(service_name)
        self.s3_service.list_object_versions.side_effect = list_object_versions_side_effect

        # Mock paginators
        self.list_object_versions_mock = MagicMock()
        self.list_object_versions_mock.paginate.side_effect = list_object_versions_paginated_side_effect
        self.list_objects_v2_mock = MagicMock()
        self.list_objects_v2_mock.paginate.side_effect = list_objects_v2_paginated_side_effect
        side_effect_map = {
            'list_object_versions': self.list_object_versions_mock,
            'list_objects_v2': self.list_objects_v2_mock
        }
        self.s3_service.get_paginator.side_effect = lambda action_name: side_effect_map.get(action_name)

    def tearDown(self):
        self.patcher.stop()

    # Test check_existence_of_objects_in_bucket

    def test_check_existence_of_objects_in_bucket_missing_bucket_name(self):
        events = {}
        self.assertRaises(KeyError, check_existence_of_objects_in_bucket, events, None)
        self.client.list_object_versions.assert_not_called()

    def test_check_existence_of_objects_in_bucket(self):
        events = {
            "S3BucketToRestoreName": S3_BUCKET
        }
        response = check_existence_of_objects_in_bucket(events, None)

        self.assertEqual("3", response['NumberOfObjectsExistInRestoreBucket'])
        self.assertEqual(True, response['AreObjectsExistInRestoreBucket'])
        self.s3_service.list_object_versions.assert_called_once()

    def test_check_existence_of_objects_in_bucket_empty(self):
        events = {
            "S3BucketToRestoreName": S3_EMPTY_BUCKET
        }
        response = check_existence_of_objects_in_bucket(events, None)

        self.assertEqual("0", response['NumberOfObjectsExistInRestoreBucket'])
        self.assertEqual(False, response['AreObjectsExistInRestoreBucket'])
        self.s3_service.list_object_versions.assert_called_once()

    # Test clean_bucket

    def test_clean_bucket_missing_bucket_name(self):
        events = {}
        self.assertRaises(KeyError, clean_bucket, events, None)
        self.list_object_versions_mock.paginate.assert_not_called()
        self.s3_service.delete_object.assert_not_called()

    def test_clean_bucket(self):
        events = {
            "S3BucketNameToClean": S3_BUCKET
        }
        response = clean_bucket(events, None)
        self.list_object_versions_mock.paginate.assert_called_once_with(Bucket=S3_BUCKET)
        self.assertEqual(6, response['NumberOfDeletedObjects'])
        self.assertEqual(6, self.s3_service.delete_object.call_count)
        self.s3_service.delete_object.assert_has_calls([
            call(Bucket=S3_BUCKET, Key="test0.txt", VersionId="null"),
            call(Bucket=S3_BUCKET, Key="test0.txt", VersionId=S3_FILE_VERSION_ID),
            call(Bucket=S3_BUCKET, Key="test_deleted0.txt", VersionId=S3_FILE_VERSION_ID),
            call(Bucket=S3_BUCKET, Key="test1.txt", VersionId="null"),
            call(Bucket=S3_BUCKET, Key="test1.txt", VersionId=S3_FILE_VERSION_ID),
            call(Bucket=S3_BUCKET, Key="test_deleted1.txt", VersionId=S3_FILE_VERSION_ID),
        ])

    def test_clean_bucket_already_empty(self):
        events = {
            "S3BucketNameToClean": S3_EMPTY_BUCKET
        }
        response = clean_bucket(events, None)
        self.list_object_versions_mock.paginate.assert_called_once_with(Bucket=S3_EMPTY_BUCKET)
        self.assertEqual(0, response['NumberOfDeletedObjects'])
        self.s3_service.delete_object.assert_not_called()

    # Test restore_from_backup

    def test_restore_from_backup_missing_buckets(self):
        events = {}
        self.assertRaises(KeyError, restore_from_backup, events, None)
        self.s3_service.copy.assert_not_called()
        self.list_objects_v2_mock.paginate.assert_not_called()

    def test_restore_from_backup_missing_source_bucket(self):
        events = {
            "S3BucketToRestoreName": S3_BUCKET
        }
        self.assertRaises(KeyError, restore_from_backup, events, None)
        self.s3_service.copy.assert_not_called()
        self.list_objects_v2_mock.paginate.assert_not_called()

    def test_restore_from_backup_missing_target_bucket(self):
        events = {
            "S3BackupBucketName": S3_BUCKET
        }
        self.assertRaises(KeyError, restore_from_backup, events, None)
        self.s3_service.copy.assert_not_called()
        self.list_objects_v2_mock.paginate.assert_not_called()

    def test_restore_from_backup(self):
        events = {
            "S3BucketToRestoreName": S3_EMPTY_BUCKET,
            "S3BackupBucketName": S3_BUCKET
        }
        response = restore_from_backup(events, None)
        self.list_objects_v2_mock.paginate.assert_called_once_with(Bucket=S3_BUCKET)
        self.assertEqual(4, response['CopiedFilesNumber'])
        self.assertEqual(4, self.s3_service.copy.call_count)
        self.s3_service.copy.assert_has_calls([
            call({'Bucket': S3_BUCKET, 'Key': 'test0_0.txt'}, S3_EMPTY_BUCKET, 'test0_0.txt'),
            call({'Bucket': S3_BUCKET, 'Key': 'test0_1.txt'}, S3_EMPTY_BUCKET, 'test0_1.txt'),
            call({'Bucket': S3_BUCKET, 'Key': 'test1_0.txt'}, S3_EMPTY_BUCKET, 'test1_0.txt'),
            call({'Bucket': S3_BUCKET, 'Key': 'test1_1.txt'}, S3_EMPTY_BUCKET, 'test1_1.txt')
        ])
        self.assertLess(0, float(response['RecoveryTimeSeconds']))

    def test_restore_from_backup_empty_source(self):
        events = {
            "S3BucketToRestoreName": S3_EMPTY_BUCKET,
            "S3BackupBucketName": S3_EMPTY_BUCKET
        }
        response = restore_from_backup(events, None)
        self.list_objects_v2_mock.paginate.assert_called_once_with(Bucket=S3_EMPTY_BUCKET)
        self.assertEqual(0, response['CopiedFilesNumber'])
        self.s3_service.copy.assert_not_called()

    # Test restore_to_the_previous_version

    def test_restore_to_the_previous_version_missing_bucket_and_key(self):
        events = {}
        self.assertRaises(KeyError, restore_to_the_previous_version, events, None)
        self.s3_service.list_object_versions.assert_not_called()
        self.s3_service.copy.assert_not_called()

    def test_restore_to_the_previous_version_missing_bucket(self):
        events = {
            "S3BucketObjectKey": "key"
        }
        self.assertRaises(KeyError, restore_to_the_previous_version, events, None)
        self.s3_service.list_object_versions.assert_not_called()
        self.s3_service.copy.assert_not_called()

    def test_restore_to_the_previous_version_missing_key(self):
        events = {
            "S3BucketName": S3_BUCKET
        }
        self.assertRaises(KeyError, restore_to_the_previous_version, events, None)
        self.s3_service.list_object_versions.assert_not_called()
        self.s3_service.copy.assert_not_called()

    def test_restore_to_the_previous_version_empty_source(self):
        events = {
            "S3BucketObjectKey": "key",
            "S3BucketName": S3_EMPTY_BUCKET
        }
        self.assertRaises(AssertionError, restore_to_the_previous_version, events, None)
        self.s3_service.list_object_versions.assert_called_once_with(Bucket=S3_EMPTY_BUCKET, Prefix="key", MaxKeys=2)
        self.s3_service.copy.assert_not_called()

    def test_restore_to_the_previous_version_object_has_no_versions(self):
        events = {
            "S3BucketObjectKey": S3_OBJECT_KEY_NO_VERSIONS,
            "S3BucketName": S3_BUCKET
        }
        self.assertRaises(AssertionError, restore_to_the_previous_version, events, None)
        self.s3_service.list_object_versions.assert_called_once_with(Bucket=S3_BUCKET, Prefix=S3_OBJECT_KEY_NO_VERSIONS,
                                                                     MaxKeys=2)
        self.s3_service.copy.assert_not_called()

    def test_restore_to_the_previous_version(self):
        events = {
            "S3BucketObjectKey": S3_OBJECT_WITH_VERSIONS,
            "S3BucketName": S3_BUCKET
        }
        response = restore_to_the_previous_version(events, None)
        self.s3_service.list_object_versions.assert_called_once_with(Bucket=S3_BUCKET, Prefix=S3_OBJECT_WITH_VERSIONS,
                                                                     MaxKeys=2)
        self.s3_service.copy.assert_called_once_with(
            {'Bucket': S3_BUCKET, 'Key': S3_OBJECT_WITH_VERSIONS, 'VersionId': S3_FILE_VERSION_ID}, S3_BUCKET,
            S3_OBJECT_WITH_VERSIONS
        )
        self.assertLess(0, float(response['RestoreTimeSeconds']))
        self.assertEqual('null', response['OldVersion'])
        self.assertEqual(S3_FILE_VERSION_ID, response['ActualVersion'])
