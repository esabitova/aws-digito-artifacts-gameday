import unittest
import pytest
from unittest.mock import MagicMock, call
from resource_manager.src.util.s3_utils import put_object, get_object, __list_objects as list_objects, \
    get_number_of_files, get_versions, clean_bucket
from documents.util.scripts.test.test_s3_util import list_objects_v2_paginated_side_effect, S3_BUCKET, \
    S3_EMPTY_BUCKET, list_object_versions_paginated_side_effect, S3_OBJECT_WITH_VERSIONS, S3_OBJECT_KEY_NO_VERSIONS, \
    S3_FILE_VERSION_ID
import resource_manager.src.util.boto3_client_factory as client_factory

S3_OBJECT_KEY = 's3-object-key'
S3_OBJECT_BODY = 'some content'
S3_VERSION_ID = 'PHtexPGjH2y.zBgT8LmB7wwLI2mpbz.k'
S3_MAX_KEYS = 4


@pytest.mark.unit_test
class TestS3Util(unittest.TestCase):

    def setUp(self):
        self.session_mock = MagicMock()
        self.mock_s3_service = MagicMock()
        self.client_side_effect_map = {
            's3': self.mock_s3_service,

        }
        self.session_mock.client.side_effect = lambda service_name, config=None: \
            self.client_side_effect_map.get(service_name)

        # Mock paginators
        self.list_object_versions_mock = MagicMock()
        self.list_object_versions_mock.paginate.side_effect = list_object_versions_paginated_side_effect
        self.list_objects_v2_mock = MagicMock()
        self.list_objects_v2_mock.paginate.side_effect = list_objects_v2_paginated_side_effect
        side_effect_map = {
            'list_object_versions': self.list_object_versions_mock,
            'list_objects_v2': self.list_objects_v2_mock
        }
        self.mock_s3_service.get_paginator.side_effect = lambda action_name: side_effect_map.get(action_name)

    def tearDown(self):
        # Clean client factory cache after each test.
        client_factory.clients = {}
        client_factory.resources = {}

    def test_put_object(self):
        put_object(self.session_mock, S3_BUCKET, S3_OBJECT_KEY, S3_OBJECT_BODY)
        self.mock_s3_service.put_object.assert_called_once_with(Bucket=S3_BUCKET,
                                                                Key=S3_OBJECT_KEY, Body=S3_OBJECT_BODY)

    def test_get_object(self):
        get_object(self.session_mock, S3_BUCKET, S3_OBJECT_KEY, S3_VERSION_ID)
        self.mock_s3_service.get_object.assert_called_once_with(Bucket=S3_BUCKET,
                                                                Key=S3_OBJECT_KEY, VersionId=S3_VERSION_ID)

    def test__list_objects(self):
        list_objects(self.session_mock, S3_BUCKET)
        self.list_objects_v2_mock.paginate.assert_called_once_with(Bucket=S3_BUCKET)

    def test_get_number_of_files(self):
        number_of_files = get_number_of_files(self.session_mock, S3_BUCKET)
        self.assertEqual(4, number_of_files)

    def test_get_number_of_files_empty_bucket(self):
        number_of_files = get_number_of_files(self.session_mock, S3_EMPTY_BUCKET)
        self.assertEqual(0, number_of_files)

    def test_get_versions(self):
        """
        Test data has two pages with one file and one additional version each
        """
        versions = get_versions(self.session_mock, S3_BUCKET, S3_OBJECT_WITH_VERSIONS, S3_MAX_KEYS)
        self.list_object_versions_mock.paginate.assert_called_once_with(
            Bucket=S3_BUCKET, Prefix=S3_OBJECT_WITH_VERSIONS, MaxKeys=S3_MAX_KEYS
        )
        self.assertEqual(4, len(versions))

    def test_get_versions_empty_bucket(self):
        versions = get_versions(self.session_mock, S3_EMPTY_BUCKET, S3_OBJECT_WITH_VERSIONS, S3_MAX_KEYS)
        self.list_object_versions_mock.paginate.assert_called_once_with(
            Bucket=S3_EMPTY_BUCKET, Prefix=S3_OBJECT_WITH_VERSIONS, MaxKeys=S3_MAX_KEYS
        )
        self.assertEqual(0, len(versions))

    def test_get_versions_file_has_no_versions(self):
        versions = get_versions(self.session_mock, S3_BUCKET, S3_OBJECT_KEY_NO_VERSIONS, S3_MAX_KEYS)
        self.list_object_versions_mock.paginate.assert_called_once_with(
            Bucket=S3_BUCKET, Prefix=S3_OBJECT_KEY_NO_VERSIONS, MaxKeys=S3_MAX_KEYS
        )
        self.assertEqual(1, len(versions))

    def test_clean_bucket_empty(self):
        clean_bucket(self.session_mock, S3_EMPTY_BUCKET)
        self.list_object_versions_mock.paginate.assert_called_once_with(Bucket=S3_EMPTY_BUCKET)
        self.mock_s3_service.delete_object.assert_not_called()

    def test_clean_bucket(self):
        clean_bucket(self.session_mock, S3_BUCKET)
        self.list_object_versions_mock.paginate.assert_called_once_with(Bucket=S3_BUCKET)
        self.assertEqual(6, self.mock_s3_service.delete_object.call_count)
        self.mock_s3_service.delete_object.assert_has_calls([
            call(Bucket=S3_BUCKET, Key="test0.txt", VersionId="null"),
            call(Bucket=S3_BUCKET, Key="test0.txt", VersionId=S3_FILE_VERSION_ID),
            call(Bucket=S3_BUCKET, Key="test_deleted0.txt", VersionId=S3_FILE_VERSION_ID),
            call(Bucket=S3_BUCKET, Key="test1.txt", VersionId="null"),
            call(Bucket=S3_BUCKET, Key="test1.txt", VersionId=S3_FILE_VERSION_ID),
            call(Bucket=S3_BUCKET, Key="test_deleted1.txt", VersionId=S3_FILE_VERSION_ID),
        ])
