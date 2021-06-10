import boto3
import unittest
import pytest
from resource_manager.src.resource_pool import ResourcePool
from resource_manager.src.cloud_formation import CloudFormationTemplate
from resource_manager.src.s3 import S3


@pytest.mark.fix_integ_test_stalled_resources
class TestFixIntegTestStalledResources(unittest.TestCase):

    def test_fix_integ_test_stalled_resources(self):
        # We are using 'Instance metadata service on an Amazon EC2 instance that has an IAM role configured'
        # in CodeCommit Pipeline: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html
        boto3_session = boto3.Session()
        aws_account_id = boto3_session.client('sts').get_caller_identity().get('Account')

        cfn_helper = CloudFormationTemplate(boto3_session)
        s3_helper = S3(boto3_session, aws_account_id)
        rm = ResourcePool(cfn_helper, s3_helper, dict(), None, None)
        rm.init_ddb_tables(boto3_session)
        rm.fix_stalled_resources()
