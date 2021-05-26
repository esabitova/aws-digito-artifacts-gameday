import unittest
import pytest
from botocore.exceptions import ClientError

import resource_manager.src.util.boto3_client_factory as client_factory
from resource_manager.src.constants import s3_bucket_name_pattern
from unittest.mock import MagicMock
from resource_manager.src.s3 import S3


@pytest.mark.unit_test
class TestS3(unittest.TestCase):

    def setUp(self):
        self.s3_existing_test_key = 's3_existing_test_key'
        self.mock_region_name = 'test_aws_region'
        self.mock_aws_account = 'test_aws_account_id'
        self.mock_s3_bucket_name = s3_bucket_name_pattern.replace('<account_id>', self.mock_aws_account)\
            .replace('<region_name>', self.mock_region_name)

        self.mock_file_name = 'test-file-name'
        self.mock_file_url = 'https://{}.s3.{}.amazonaws.com/{}'.format(self.mock_s3_bucket_name,
                                                                        self.mock_region_name,
                                                                        self.mock_file_name)
        self.session_mock = MagicMock()
        self.session_mock.configure_mock(region_name=self.mock_region_name)

        self.mock_sts_service = MagicMock()
        self.mock_s3_service = MagicMock()
        self.client_side_effect_map = {
            'sts': self.mock_sts_service,
            's3': self.mock_s3_service
        }
        self.session_mock.client.side_effect = lambda service_name, config=None: \
            self.client_side_effect_map.get(service_name)
        self.mock_sts_service.get_caller_identity.return_value = dict(Account=self.mock_aws_account)

        self.mock_s3_resource = MagicMock()
        self.resource_side_effect_map = {
            's3': self.mock_s3_resource
        }
        self.session_mock.resource.side_effect = lambda service_name, config=None: \
            self.resource_side_effect_map.get(service_name)

        self.s3_helper = S3(self.session_mock)

    def tearDown(self):
        # Clean client factory cache after each test.
        client_factory.clients = {}
        client_factory.resources = {}

    def test_get_bucket_name_success(self):
        self.assertEqual(self.mock_s3_bucket_name, self.s3_helper.get_bucket_name())

    def test_bucket_key_exist_success(self):
        mock_object = MagicMock()
        mock_object.configure_mock(key=self.s3_existing_test_key)
        mock_objects = MagicMock()
        mock_objects.all.return_value = [mock_object]
        mock_bucket = MagicMock()
        mock_bucket.configure_mock(objects=mock_objects)
        self.mock_s3_resource.Bucket.return_value = mock_bucket

        self.assertTrue(self.s3_helper.bucket_key_exist(self.s3_helper.get_bucket_name(), self.s3_existing_test_key))

    def test_s3_bucket_exists_exist_success(self):
        mock_existing_bucket = MagicMock()
        mock_existing_bucket.configure_mock(name=self.mock_s3_bucket_name)
        self.mock_s3_resource.buckets.all.return_value = [mock_existing_bucket]
        self.assertTrue(self.s3_helper.bucket_exists(self.mock_s3_bucket_name))

    def test_s3_bucket_exists_not_exist_success(self):
        mock_existing_bucket = MagicMock()
        mock_existing_bucket.configure_mock(name='test_bucket_name')
        self.mock_s3_resource.buckets.all.return_value = [mock_existing_bucket]
        self.assertFalse(self.s3_helper.bucket_exists(self.mock_s3_bucket_name))

    def test_s3_init_no_existing_bucket_success(self):
        # Result - bucket does not exist and will be created
        mock_existing_bucket = MagicMock()
        mock_existing_bucket.configure_mock(name='test_bucket_name')
        self.mock_s3_resource.buckets.all.return_value = [mock_existing_bucket]
        mock_s3_object = MagicMock()
        mock_s3_object.configure_mock(name='test_s3_object')
        self.mock_s3_resource.Object.return_value = mock_s3_object
        self.mock_s3_service.generate_presigned_url.return_value = self.mock_file_url

        actual_s3_file_name = self.s3_helper.upload_file(self.mock_file_name, {'key': 'val'})

        self.assertEqual(actual_s3_file_name, self.mock_file_url)
        self.mock_s3_service.create_bucket.assert_called_once()
        mock_s3_object.put.assert_called_once()
        self.mock_s3_service.generate_presigned_url.assert_called_once()

    def test_s3_init_with_existing_bucket_success(self):
        # Result - bucket exist and will NOT be created
        mock_existing_bucket = MagicMock()
        mock_existing_bucket.configure_mock(name=self.mock_s3_bucket_name)
        self.mock_s3_resource.buckets.all.return_value = [mock_existing_bucket]
        mock_s3_object = MagicMock()
        mock_s3_object.configure_mock(name='test_s3_object')
        self.mock_s3_resource.Object.return_value = mock_s3_object

        self.mock_s3_service.generate_presigned_url.return_value = "pre_signed_url"
        actual_s3_file_name = self.s3_helper.upload_file(self.mock_file_name, {'key': 'val'})

        self.assertEqual(actual_s3_file_name, "pre_signed_url")
        self.mock_s3_service.create_bucket.assert_not_called()
        mock_s3_object.put.assert_called_once()
        self.mock_s3_service.generate_presigned_url.assert_called_once()

    def test_delete_bucket_success(self):
        # Result - bucket exist, all files will be deleted together with bucket
        mock_objects = MagicMock()
        mock_bucket = MagicMock()
        delete_function = MagicMock()
        self.mock_s3_resource.Bucket.return_value = mock_bucket

        mock_bucket.configure_mock(objects=mock_objects)
        mock_objects.configure_mock(delete=delete_function)

        mock_existing_bucket = MagicMock()
        mock_existing_bucket.configure_mock(name=self.mock_s3_bucket_name)
        self.mock_s3_resource.buckets.all.return_value = [mock_existing_bucket]

        self.s3_helper.delete_bucket(self.mock_s3_bucket_name)

        delete_function.assert_called_once()
        self.mock_s3_service.delete_bucket.assert_called_once()

    def test_s3_upload_file_client_error(self):
        mock_existing_bucket = MagicMock()
        mock_existing_bucket.configure_mock(name=self.mock_s3_bucket_name)
        self.mock_s3_resource.buckets.all.return_value = [mock_existing_bucket]

        mock_s3_object = MagicMock()
        mock_s3_object.configure_mock(**{'name.return_value': 'test_s3_object',
                                         'put.side_effect': ClientError({}, "put")
                                         })
        self.mock_s3_resource.Object.return_value = mock_s3_object

        with pytest.raises(ClientError):
            self.s3_helper.upload_file(self.mock_file_name, {'key': 'val'})

    def test_bucket_key_exist_true(self):
        self.mock_s3_service.head_object.return_value = MagicMock()
        key_exists = self.s3_helper.bucket_key_exist("test_bucket", "test_file")
        self.assertTrue(key_exists)

    def test_bucket_key_exist_false(self):
        self.mock_s3_service.head_object.side_effect = ClientError({}, "ops")
        key_exists = self.s3_helper.bucket_key_exist("test_bucket", "test_file")
        self.assertFalse(key_exists)
