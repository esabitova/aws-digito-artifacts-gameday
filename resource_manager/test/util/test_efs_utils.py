import unittest
import pytest
from unittest.mock import MagicMock
import resource_manager.src.util.boto3_client_factory as client_factory
import resource_manager.src.util.efs_utils as efs_utils
from documents.util.scripts.test.test_data_provider import \
    ACCOUNT_ID, \
    get_sample_describe_file_systems_response


@pytest.mark.unit_test
class TestEfsUtil(unittest.TestCase):

    def setUp(self):
        self.session_mock = MagicMock()
        self.mock_efs_service = MagicMock()
        self.client_side_effect_map = {
            'efs': self.mock_efs_service
        }
        self.session_mock.client.side_effect = lambda service_name, config=None: \
            self.client_side_effect_map.get(service_name)

    def tearDown(self):
        # Clean client factory cache after each test.
        client_factory.clients = {}
        client_factory.resources = {}

    def test_describe_filesystem(self):
        fs_id = "TestFsID"
        mock_describe_fs_result = \
            {'FileSystems': [{
                "FileSystemArn": f"arn:aws:elasticfilesystem:eu-south-1:{ACCOUNT_ID}:file-system/{fs_id}"
            }]}
        self.mock_efs_service.describe_file_systems.return_value = get_sample_describe_file_systems_response(fs_id)
        result = efs_utils.describe_filesystem(self.session_mock, fs_id)
        self.mock_efs_service.describe_file_systems.assert_called_once_with(FileSystemId=fs_id)
        self.assertEqual(result['FileSystems'][0]['FileSystemArn'],
                         mock_describe_fs_result['FileSystems'][0]['FileSystemArn'])

    def test_delete_filesystem(self):
        fs_id = "TestFsID"
        self.mock_efs_service. \
            delete_file_system. \
            return_value = None
        efs_utils.delete_filesystem(self.session_mock, fs_id)
        self.mock_efs_service.delete_file_system. \
            assert_called_once_with(FileSystemId=fs_id)
