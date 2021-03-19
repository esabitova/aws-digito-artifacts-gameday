import boto3
import unittest
import pytest
from resource_manager.src.resource_manager import ResourceManager
from resource_manager.src.cloud_formation import CloudFormationTemplate
from resource_manager.src.s3 import S3


@pytest.mark.fix_integ_test_stalled_resources
class TestFixIntegTestStalledResources(unittest.TestCase):

    def test_fix_integ_test_stalled_resources(self):
        boto3_session = boto3.Session(profile_name='default')
        cfn_helper = CloudFormationTemplate(boto3_session)
        s3_helper = S3(boto3_session)
        rm = ResourceManager(cfn_helper, s3_helper)
        rm.init_ddb_tables(boto3_session)
        rm.fix_stalled_resources()
