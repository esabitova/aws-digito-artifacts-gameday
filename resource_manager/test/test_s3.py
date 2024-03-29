import unittest
import pytest
import resource_manager.src.util.boto3_client_factory as client_factory
import os.path

from resource_manager.src.constants import s3_bucket_name_pattern
from unittest.mock import MagicMock
from resource_manager.src.s3 import S3
from botocore.exceptions import ClientError


def get_local_file(file_name):
    if os.path.isfile(f'{file_name}'):
        return f'{file_name}'
    else:
        return f'resource_manager/test/{file_name}'


@pytest.mark.unit_test
class TestS3(unittest.TestCase):

    def setUp(self):
        self.s3_existing_test_key = 's3_existing_test_key'
        self.mock_region_name = 'test_aws_region'
        self.mock_aws_account = 'test_aws_account_id'
        self.mock_s3_bucket_name = s3_bucket_name_pattern.replace('<account_id>', self.mock_aws_account) \
            .replace('<region_name>', self.mock_region_name)

        self.mock_file_name = 'test-file-name'
        self.mock_file_url = 'https://{}.s3.{}.amazonaws.com/{}'.format(self.mock_s3_bucket_name,
                                                                        self.mock_region_name,
                                                                        self.mock_file_name)
        self.session_mock = MagicMock()
        self.session_mock.configure_mock(region_name=self.mock_region_name)
        self.session_mock_east1 = MagicMock()
        self.session_mock_east1.configure_mock(region_name='us-east-1')

        self.mock_s3_service = MagicMock()
        self.client_side_effect_map = {
            's3': self.mock_s3_service
        }
        self.session_mock.client.side_effect = lambda service_name, config=None: \
            self.client_side_effect_map.get(service_name)

        self.mock_s3_resource = MagicMock()
        self.resource_side_effect_map = {
            's3': self.mock_s3_resource
        }
        self.session_mock.resource.side_effect = lambda service_name, config=None: \
            self.resource_side_effect_map.get(service_name)

        self.s3_helper = S3(self.session_mock, self.mock_aws_account)
        self.s3_helper_east1 = S3(self.session_mock_east1, self.mock_aws_account)

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

    def test_delete_bucket_bucket_versioning_disabled_success(self):
        # Result - bucket exist, all files will be deleted together with bucket
        mock_objects = MagicMock()
        mock_bucket = MagicMock()
        delete_function = MagicMock()
        mock_bucket_version = MagicMock()
        mock_bucket_version.configure_mock(status='Disabled')
        mock_object_versions_del_func = MagicMock()
        mock_object_versions = MagicMock()
        mock_object_versions.configure_mock(delete=mock_object_versions_del_func)
        self.mock_s3_resource.Bucket.return_value = mock_bucket
        self.mock_s3_resource.BucketVersioning.return_value = mock_bucket_version

        mock_bucket.configure_mock(objects=mock_objects, object_versions=mock_object_versions)
        mock_objects.configure_mock(delete=delete_function)

        mock_existing_bucket = MagicMock()
        mock_existing_bucket.configure_mock(name=self.mock_s3_bucket_name)
        self.mock_s3_resource.buckets.all.return_value = [mock_existing_bucket]

        self.s3_helper.delete_bucket(self.mock_s3_bucket_name)

        mock_object_versions_del_func.assert_not_called()
        delete_function.assert_called_once()
        self.mock_s3_service.delete_bucket.assert_called_once()

    def test_delete_bucket_bucket_versioning_enabled_success(self):
        # Result - bucket exist, all files will be deleted together with bucket
        mock_objects = MagicMock()
        mock_bucket = MagicMock()
        delete_function = MagicMock()
        mock_bucket_version = MagicMock()
        mock_bucket_version.configure_mock(status='Enabled')
        mock_object_versions_del_func = MagicMock()
        mock_object_versions = MagicMock()
        mock_object_versions.configure_mock(delete=mock_object_versions_del_func)
        self.mock_s3_resource.Bucket.return_value = mock_bucket
        self.mock_s3_resource.BucketVersioning.return_value = mock_bucket_version

        mock_bucket.configure_mock(objects=mock_objects, object_versions=mock_object_versions)
        mock_objects.configure_mock(delete=delete_function)

        mock_existing_bucket = MagicMock()
        mock_existing_bucket.configure_mock(name=self.mock_s3_bucket_name)
        self.mock_s3_resource.buckets.all.return_value = [mock_existing_bucket]

        self.s3_helper.delete_bucket(self.mock_s3_bucket_name)

        mock_object_versions_del_func.assert_called_once()
        delete_function.assert_not_called()
        self.mock_s3_service.delete_bucket.assert_called_once()

    def test_delete_bucket_bucket_error(self):
        # Result - bucket exist, all files will be deleted together with bucket
        mock_objects = MagicMock()
        mock_bucket = MagicMock()
        delete_function = MagicMock()
        mock_bucket_version = MagicMock()
        mock_bucket_version.configure_mock(status='Disabled')
        mock_object_versions_del_func = MagicMock()
        mock_object_versions = MagicMock()
        mock_object_versions.configure_mock(delete=mock_object_versions_del_func)
        self.mock_s3_resource.Bucket.return_value = mock_bucket
        self.mock_s3_resource.BucketVersioning.return_value = mock_bucket_version

        mock_bucket.configure_mock(objects=mock_objects, object_versions=mock_object_versions)
        mock_objects.configure_mock(delete=delete_function)

        mock_existing_bucket = MagicMock()
        mock_existing_bucket.configure_mock(name=self.mock_s3_bucket_name)
        self.mock_s3_resource.buckets.all.return_value = [mock_existing_bucket]
        self.mock_s3_service.delete_bucket.side_effect = ClientError(
            error_response={'Error': {'Type': 'Sender', 'Code': 'ERR'}},
            operation_name='DeleteBucket')
        with pytest.raises(ClientError):
            self.s3_helper.delete_bucket(self.mock_s3_bucket_name)

        mock_object_versions_del_func.assert_not_called()
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

    def test_upload_local_file_to_account_unique_bucket_passed_wo_postfix(self):
        # Result - bucket NOT exist and passed to helper method and will be created
        self.mock_s3_resource.buckets.all.return_value = []
        mock_s3_object = MagicMock()
        mock_s3_object.configure_mock(name='test_s3_object')
        self.mock_s3_resource.Object.return_value = mock_s3_object

        self.mock_s3_service.generate_presigned_url.return_value = "pre_signed_url"
        url, bucket_name, object_key, version_id = \
            self.s3_helper.upload_local_file_to_account_unique_bucket(
                self.mock_file_name,
                get_local_file('local_file_to_upload.txt'),
                'test')
        self.assertEqual(url, "pre_signed_url")
        self.mock_s3_service.create_bucket.assert_called_once_with(
            ACL='private',
            Bucket='test-test_aws_account_id-test_aws_region',
            CreateBucketConfiguration={'LocationConstraint': 'test_aws_region'}
        )
        self.mock_s3_service.put_object.assert_called_once()
        self.mock_s3_service.generate_presigned_url.assert_called_once()

    def test_upload_local_file_to_account_unique_bucket_passed_with_postfix(self):
        # Result - bucket NOT exist and passed to helper method and will be created
        self.mock_s3_resource.buckets.all.return_value = []
        mock_s3_object = MagicMock()
        mock_s3_object.configure_mock(name='test_s3_object')
        self.mock_s3_resource.Object.return_value = mock_s3_object

        self.mock_s3_service.generate_presigned_url.return_value = "pre_signed_url"
        url, bucket_name, object_key, version_id = \
            self.s3_helper.upload_local_file_to_account_unique_bucket(
                self.mock_file_name,
                get_local_file('local_file_to_upload.txt'),
                'test-test_aws_account_id-test_aws_region')
        self.assertEqual(url, "pre_signed_url")
        self.mock_s3_service.create_bucket.assert_called_once_with(
            ACL='private',
            Bucket='test-test_aws_account_id-test_aws_region',
            CreateBucketConfiguration={'LocationConstraint': 'test_aws_region'}
        )
        self.mock_s3_service.put_object.assert_called_once()
        self.mock_s3_service.generate_presigned_url.assert_called_once()

    def test_upload_local_file_if_bucket_exist(self):
        # Result - bucket exist and will NOT be created
        mock_existing_bucket = MagicMock()
        mock_existing_bucket.configure_mock(name=self.mock_s3_bucket_name)
        self.mock_s3_resource.buckets.all.return_value = [mock_existing_bucket]
        mock_s3_object = MagicMock()
        mock_s3_object.configure_mock(name='test_s3_object')
        self.mock_s3_resource.Object.return_value = mock_s3_object

        self.mock_s3_service.generate_presigned_url.return_value = "pre_signed_url"
        url, bucket_name, object_key, version_id = \
            self.s3_helper.upload_local_file(self.mock_file_name,
                                             get_local_file('local_file_to_upload.txt')
                                             )

        self.assertEqual(url, "pre_signed_url")
        self.mock_s3_service.create_bucket.assert_not_called()
        self.mock_s3_service.put_object.assert_called_once()
        self.mock_s3_service.generate_presigned_url.assert_called_once()

    def test_upload_local_file_if_bucket_passed_with_postfix(self):
        # Result - bucket exist and passed to helper method and will NOT be created
        mock_existing_bucket = MagicMock()
        mock_existing_bucket.configure_mock(name=self.mock_s3_bucket_name)
        self.mock_s3_resource.buckets.all.return_value = [mock_existing_bucket]
        mock_s3_object = MagicMock()
        mock_s3_object.configure_mock(name='test_s3_object')
        self.mock_s3_resource.Object.return_value = mock_s3_object

        self.mock_s3_service.generate_presigned_url.return_value = "pre_signed_url"
        url, bucket_name, object_key, version_id = \
            self.s3_helper.upload_local_file(self.mock_file_name,
                                             get_local_file('local_file_to_upload.txt'),
                                             self.mock_s3_bucket_name)

        self.assertEqual(url, "pre_signed_url")
        self.mock_s3_service.create_bucket.assert_not_called()
        self.mock_s3_service.put_object.assert_called_once()
        self.mock_s3_service.generate_presigned_url.assert_called_once()

    def test_upload_local_file_if_bucket_not_exist(self):
        # Result - bucket exist and will NOT be created
        mock_existing_bucket = MagicMock()
        mock_existing_bucket.configure_mock(name=self.mock_s3_bucket_name)
        self.mock_s3_resource.buckets.all.return_value = [mock_existing_bucket]
        mock_s3_object = MagicMock()
        mock_s3_object.configure_mock(name='test_s3_object')
        self.mock_s3_resource.Object.return_value = mock_s3_object

        self.mock_s3_service.generate_presigned_url.return_value = "pre_signed_url"
        url, bucket_name, object_key, version_id = \
            self.s3_helper.upload_local_file(self.mock_file_name,
                                             get_local_file('local_file_to_upload.txt'))

        self.assertEqual(url, "pre_signed_url")
        self.mock_s3_service.create_bucket.assert_not_called()
        self.mock_s3_service.put_object.assert_called_once()
        self.mock_s3_service.generate_presigned_url.assert_called_once()

    def test_upload_local_file_if_bucket_not_exist_east1(self):
        # Result - bucket exist and will NOT be created
        mock_existing_bucket = MagicMock()
        mock_existing_bucket.configure_mock(name=self.mock_s3_bucket_name)
        self.mock_s3_resource.buckets.all.return_value = []
        mock_s3_object = MagicMock()
        mock_s3_object.configure_mock(name='test_s3_object')
        self.mock_s3_resource.Object.return_value = mock_s3_object

        self.mock_s3_service.generate_presigned_url.return_value = "pre_signed_url"
        url, bucket_name, object_key, version_id = \
            self.s3_helper_east1.upload_local_file(self.mock_file_name,
                                                   get_local_file('local_file_to_upload.txt'))

        self.assertEqual(url, "pre_signed_url")
        self.mock_s3_service.create_bucket.assert_called_once_with(
            ACL='private',
            Bucket=bucket_name
        )
        self.mock_s3_service.put_object.assert_called_once()
        self.mock_s3_service.generate_presigned_url.assert_called_once()

    def test_upload_local_file_already_owned(self):
        mock_existing_bucket = MagicMock()
        mock_existing_bucket.configure_mock(name=self.mock_s3_bucket_name)
        self.mock_s3_resource.buckets.all.return_value = []

        mock_s3_object = MagicMock()
        mock_s3_object.configure_mock(name='test_s3_object')
        self.mock_s3_service.generate_presigned_url.return_value = "pre_signed_url"

        self.mock_s3_service.create_bucket.side_effect = ClientError(
            error_response={'Error': {'Type': 'Sender', 'Code': 'BucketAlreadyOwnedByYou'}},
            operation_name='CreateBucket')

        self.mock_s3_resource.Object.return_value = mock_s3_object

        url, bucket_name, object_key, version_id = self.s3_helper.upload_local_file(
            self.mock_file_name,
            get_local_file('local_file_to_upload.txt')
        )
        self.assertEqual(url, "pre_signed_url")
        self.mock_s3_service.create_bucket.assert_called_once_with(
            ACL='private',
            Bucket=bucket_name,
            CreateBucketConfiguration={'LocationConstraint': 'test_aws_region'}
        )
        self.mock_s3_service.put_object.assert_called_once()
        self.mock_s3_service.generate_presigned_url.assert_called_once()

    def test_upload_local_file_client_error_on_put_object(self):
        mock_existing_bucket = MagicMock()
        mock_existing_bucket.configure_mock(name=self.mock_s3_bucket_name)
        self.mock_s3_resource.buckets.all.return_value = [mock_existing_bucket]

        mock_s3_object = MagicMock()
        mock_s3_object.configure_mock(name='test_s3_object')

        self.mock_s3_service.put_object.side_effect = ClientError({}, "put_object")
        self.mock_s3_resource.Object.return_value = mock_s3_object

        with pytest.raises(ClientError):
            self.s3_helper.upload_local_file(self.mock_file_name,
                                             get_local_file('local_file_to_upload.txt'))

    def test_upload_local_file_client_error_on_bucket_create(self):
        mock_existing_bucket = MagicMock()
        mock_existing_bucket.configure_mock(name=self.mock_s3_bucket_name)
        self.mock_s3_resource.buckets.all.return_value = []

        mock_s3_object = MagicMock()
        mock_s3_object.configure_mock(name='test_s3_object')

        self.mock_s3_service.create_bucket.side_effect = ClientError(
            error_response={'Error': {'Type': 'Sender', 'Code': 'ZZZZ'}},
            operation_name='CreateBucket'
        )
        self.mock_s3_resource.Object.return_value = mock_s3_object

        with pytest.raises(ClientError):
            self.s3_helper.upload_local_file(self.mock_file_name,
                                             get_local_file('local_file_to_upload.txt'))

    def test_retrieve_object_metadata(self):
        mock_existing_bucket = MagicMock()
        mock_existing_bucket.configure_mock(name=self.mock_s3_bucket_name)

        mock_s3_object = MagicMock()
        mock_s3_object.configure_mock(name='test_s3_object')
        self.mock_s3_service.generate_presigned_url.return_value = "pre_signed_url"
        self.mock_s3_service.head_object.return_value = {
            'a': 'b'
        }
        res = self.s3_helper.retrieve_object_metadata(self.mock_s3_bucket_name, self.mock_file_name)

        self.assertEqual({'Object': {'a': 'b'}, 'Uri': 'pre_signed_url'}, res)
        self.mock_s3_service.head_object.assert_called_once_with(
            Bucket=self.mock_s3_bucket_name,
            Key=self.mock_file_name,
        )
        self.mock_s3_service.generate_presigned_url.assert_called_once_with(
            'get_object',
            Params={
                'Bucket': self.mock_s3_bucket_name,
                'Key': self.mock_file_name
            },
            ExpiresIn=3600
        )

    def test_retrieve_object_metadata_error(self):
        mock_existing_bucket = MagicMock()
        mock_existing_bucket.configure_mock(name=self.mock_s3_bucket_name)

        mock_s3_object = MagicMock()
        mock_s3_object.configure_mock(name='test_s3_object')
        self.mock_s3_service.generate_presigned_url.return_value = "pre_signed_url"
        self.mock_s3_service.head_object.side_effect = ClientError(
            error_response={'Error': {'Type': 'Sender', 'Code': 'ZZZZ'}},
            operation_name='CreateBucket'
        )
        with pytest.raises(ClientError):
            self.s3_helper.retrieve_object_metadata(self.mock_s3_bucket_name, self.mock_file_name)
