import unittest
import pytest
from unittest.mock import patch
from unittest.mock import MagicMock
from unittest.mock import PropertyMock
from resource_manager.src.s3 import S3


@pytest.mark.unit_test
class TestS3(unittest.TestCase):

    def setUp(self):
        self.s3_existing_test_key = 's3_existing_test_key'
        self.mock_region_name = 'test_aws_region'
        self.mock_aws_account = 'test_aws_account_id'
        self.mock_s3_bucket_name = 'ssm-test-resources-{}-{}'.format(self.mock_aws_account,
                                                                     self.mock_region_name)

        self.mock_file_name = 'test-file-name'
        self.mock_file_url = 'https://{}.s3-{}.amazonaws.com/{}'.format(self.mock_s3_bucket_name,
                                                                        self.mock_region_name,
                                                                        self.mock_file_name)
        self.client_patcher = patch('boto3.client')
        self.client = self.client_patcher.start()
        self.mock_sts_service = MagicMock()
        self.mock_s3_service = MagicMock()
        self.client_side_effect_map = {
            'sts': self.mock_sts_service,
            's3': self.mock_s3_service
        }
        self.client.side_effect = lambda service_name: self.client_side_effect_map.get(service_name)
        self.mock_sts_service.get_caller_identity.return_value = dict(Account=self.mock_aws_account)

        self.resource_patcher = patch('boto3.resource')
        self.s3_resource = self.resource_patcher.start()
        self.mock_s3_resource = MagicMock()
        self.resource_side_effect_map = {
            's3': self.mock_s3_resource
        }
        self.s3_resource.side_effect = lambda service_name: self.resource_side_effect_map.get(service_name)

        self.region_patcher = patch('boto3.session.Session.region_name', new_callable=PropertyMock)
        self.mock_region = self.region_patcher.start()
        self.mock_region.return_value = self.mock_region_name

    def tearDown(self):
        self.resource_patcher.stop()
        self.client_patcher.stop()
        self.region_patcher.stop()

    def test_get_bucket_name_success(self):
        self.assertEqual(self.mock_s3_bucket_name, S3.get_bucket_name())

    def test_get_bucket_keys_exist_success(self):
        mock_object = MagicMock()
        mock_object.configure_mock(key=self.s3_existing_test_key)
        mock_objects = MagicMock()
        mock_objects.all.return_value = [mock_object]
        mock_bucket = MagicMock()
        mock_bucket.configure_mock(objects=mock_objects)
        self.mock_s3_resource.Bucket.return_value = mock_bucket

        keys = S3.get_bucket_keys(S3.get_bucket_name())

        self.assertEqual(len(keys), 1)
        self.assertEqual(keys[0], self.s3_existing_test_key)

    def test_get_bucket_keys_no_keys_success(self):
        mock_objects = MagicMock()
        mock_objects.all.return_value = []
        mock_bucket = MagicMock()
        mock_bucket.configure_mock(objects=mock_objects)
        self.mock_s3_resource.Bucket.return_value = mock_bucket

        keys = S3.get_bucket_keys(S3.get_bucket_name())

        self.assertEqual(len(keys), 0)

    def test_bucket_key_exist_success(self):
        mock_object = MagicMock()
        mock_object.configure_mock(key=self.s3_existing_test_key)
        mock_objects = MagicMock()
        mock_objects.all.return_value = [mock_object]
        mock_bucket = MagicMock()
        mock_bucket.configure_mock(objects=mock_objects)
        self.mock_s3_resource.Bucket.return_value = mock_bucket

        self.assertTrue(S3.bucket_key_exist(S3.get_bucket_name(), self.s3_existing_test_key))

    def test_s3_bucket_exists_exist_success(self):
        mock_existing_bucket = MagicMock()
        mock_existing_bucket.configure_mock(name=self.mock_s3_bucket_name)
        self.mock_s3_resource.buckets.all.return_value = [mock_existing_bucket]
        self.assertTrue(S3.bucket_exists(self.mock_s3_bucket_name))

    def test_s3_bucket_exists_not_exist_success(self):
        mock_existing_bucket = MagicMock()
        mock_existing_bucket.configure_mock(name='test_bucket_name')
        self.mock_s3_resource.buckets.all.return_value = [mock_existing_bucket]
        self.assertFalse(S3.bucket_exists(self.mock_s3_bucket_name))

    def test_S3_init_no_existing_bucket_success(self):
        # Result - bucket does not exist and will be created
        mock_existing_bucket = MagicMock()
        mock_existing_bucket.configure_mock(name='test_bucket_name')
        self.mock_s3_resource.buckets.all.return_value = [mock_existing_bucket]

        actual_s3_file_name = S3.upload_file(self.mock_file_name)

        self.assertEqual(actual_s3_file_name, self.mock_file_url)
        self.mock_s3_service.create_bucket.assert_called_once()
        self.mock_s3_service.upload_file.assert_called_once()

    def test_S3_init_with_existing_bucket_success(self):
        # Result - bucket exist and will NOT be created
        mock_existing_bucket = MagicMock()
        mock_existing_bucket.configure_mock(name=self.mock_s3_bucket_name)
        self.mock_s3_resource.buckets.all.return_value = [mock_existing_bucket]

        actual_s3_file_name = S3.upload_file(self.mock_file_name)

        self.assertEqual(actual_s3_file_name, self.mock_file_url)
        self.mock_s3_service.create_bucket.assert_not_called()
        self.mock_s3_service.upload_file.assert_called_once()

    def test_delete_bucket_success(self):
        # Result - bucket exist, all files will be deleted together with bucket
        mock_object = MagicMock()
        mock_object.configure_mock(key=self.s3_existing_test_key)
        mock_objects = MagicMock()
        mock_objects.all.return_value = [mock_object]
        mock_bucket = MagicMock()
        mock_bucket.configure_mock(objects=mock_objects)
        self.mock_s3_resource.Bucket.return_value = mock_bucket

        mock_existing_bucket = MagicMock()
        mock_existing_bucket.configure_mock(name=self.mock_s3_bucket_name)
        self.mock_s3_resource.buckets.all.return_value = [mock_existing_bucket]

        S3.delete_bucket(self.mock_s3_bucket_name)

        self.mock_s3_service.delete_objects.assert_called_once()
        self.mock_s3_service.delete_bucket.assert_called_once()
