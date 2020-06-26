#
# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

import os
import sys
import time
import unittest
import json

DOC_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


# Import shared testing code
sys.path.append(
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))),
        'TestingFramework'
    )
)
import ssm_testing  # noqa pylint: disable=import-error,wrong-import-position
import test_document_base

RESOURCE_BASE_NAME = 'FailoverAuroraCluster'

TEST_DB_CLASS = 'db.r4.large'
TEST_DB_ALLOCATED_STORAGE = '20'
TEST_DB_MASTER_USERNAME = 'test_root'
TEST_DB_MASTER_USER_PASSWORD = 'Password123'

class DocumentTest(unittest.TestCase, test_document_base.DocumentTestBase):

    @classmethod
    def setUpClass(cls):

        test_document_base.DocumentTestBase.__init__(cls, RESOURCE_BASE_NAME)
        cls.sts_client = cls.service_client_provider.get_sts_client()
        cls.cfn_client = cls.service_client_provider.get_cfn_client()
        cls.ssm_client = cls.service_client_provider.get_ssm_client()
        cls.rds_client = cls.service_client_provider.get_rds_client()
        cls.s3_client = cls.service_client_provider.get_s3_client()
        cls.s3_resource = cls.service_client_provider.get_s3_resource()

        cls.document_name = cls.config.get_resource_name(RESOURCE_BASE_NAME)

        cls.stack_name = cls.config.get_resource_name(RESOURCE_BASE_NAME)

        cls.cfn_tester = cls.get_cfn_tester()
        cls.ssm_tester = cls.get_ssm_tester()

        cls.create_test_stack(cls.cfn_tester)

        cls.db_cluster_id = cls.cfn_tester.stack_outputs['DatabaseClusterId']

        # Verify role exists
        cls.role_arn = cls.cfn_tester.stack_outputs['AutomationAssumeRoleARN']
        cls.verify_role_created(cls.role_arn)

        cls.ssm_tester.create_document()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.clean_up()
        except Exception as ex:
            cls.logger.info("Clean up failed - " + str(ex))
            pass
        cls.ssm_tester.destroy()
        cls.cfn_tester.delete_stack()


    @classmethod
    def get_ssm_tester(cls):
        ssm_tester = ssm_testing.SSMTester(
            ssm_client=cls.ssm_client,
            doc_filename=os.path.join(DOC_DIR,'Documents/Digito-AuroraFailoverCluster.yml'),
            doc_name=cls.document_name,
            doc_type='Automation',
            logger=cls.logger,
            doc_format = 'YAML'
        )
        return ssm_tester

    @classmethod
    def get_cfn_tester(cls):
        cfn_tester = ssm_testing.CFNTester(
            cfn_client=cls.cfn_client,
            template_filename=os.path.abspath(os.path.join(
                DOC_DIR,"Tests/CloudFormationTemplates/TestTemplate.yml")),
            stack_name=cls.stack_name,
            logger=cls.logger
        )
        return cfn_tester

    @classmethod
    def create_test_stack(cls, cfn_tester):
        cfn_tester.create_stack([
            {
                'ParameterKey': 'UserARN',
                'ParameterValue': cls.sts_client.get_caller_identity().get('Arn')
            },
            {
                'ParameterKey': 'DBInstanceClass',
                'ParameterValue': TEST_DB_CLASS
            },
            {
                'ParameterKey': 'AllocatedStorage',
                'ParameterValue': TEST_DB_ALLOCATED_STORAGE
            },
            {
                'ParameterKey': 'MasterUsername',
                'ParameterValue': TEST_DB_MASTER_USERNAME
            },
            {
                'ParameterKey': 'MasterUserPassword',
                'ParameterValue': TEST_DB_MASTER_USER_PASSWORD
            }
        ])

    @classmethod
    def verify_role_created(cls, role_arn):
        cls.logger.info("Verifying that role exists: " + role_arn)
        # For what ever reason assuming a role that got created too fast fails, so we just wait until we can.
        retry_count = 12
        while True:
            try:
                cls.sts_client.assume_role(RoleArn=role_arn, RoleSessionName="checking_assume")
                break
            except Exception as e:
                retry_count -= 1
                if retry_count == 0:
                    raise e

                cls.logger.info("Unable to assume role... trying again in 5 sec")
                time.sleep(5)

    def execute_document_default(self, ssm_tester, cluster_id, role_arn):
        execution_id = ssm_tester.execute_automation(
            params={'ClusterId': [cluster_id],
                    'AutomationAssumeRole': [role_arn]})
        return execution_id

    def execute_document_with_primary(self, ssm_tester, cluster_id, instance_id, role_arn):
        execution_id = ssm_tester.execute_automation(
            params={'ClusterId': [cluster_id],
                    'InstanceId': [instance_id],
                    'AutomationAssumeRole': [role_arn]})
        return execution_id

    def get_automation_outputs(self, execution_id):
        output = self.ssm_client.get_automation_execution(AutomationExecutionId=execution_id)['AutomationExecution']['Outputs']['RunCfnLintAgainstTemplate.output'][0]
        return output


    def get_reader_writer(self, db_cluster_id):
        db_cluster_state = self.rds_client.describe_db_clusters(DBClusterIdentifier=db_cluster_id)
        db_instances = db_cluster_state['DBClusters'][0]['DBClusterMembers']

        for db_instance  in db_instances:
            if db_instance['IsClusterWriter']:
                db_writer = db_instance['DBInstanceIdentifier']
            else:
                db_reader = db_instance['DBInstanceIdentifier']

        return (db_reader, db_writer)

    def test_failover_default(self):

        db_reader, db_writer = self.get_reader_writer(self.db_cluster_id)

        try:
            execution_id_default  = self.execute_document_default(self.ssm_tester, self.db_cluster_id,
                                                                  self.role_arn)
            self.assertEqual(self.ssm_tester.automation_execution_status(execution_id_default, False), 'Success')
            time.sleep(20)

            new_reader, new_writer = self.get_reader_writer(self.db_cluster_id)
            self.assertEqual(db_reader, new_writer)
            self.assertEqual(db_writer, new_reader)

        except Exception as ex:
            self.logger.info("Test failed - " + str(ex))
            raise ex

    def test_failover_with_primary(self):
        db_reader, db_writer = self.get_reader_writer(self.db_cluster_id)

        try:
            execution_id_primary  = self.execute_document_with_primary(self.ssm_tester, self.db_cluster_id,
                                                                       db_reader,self.role_arn)
            self.assertEqual(self.ssm_tester.automation_execution_status(execution_id_primary, False), 'Success')
            time.sleep(20)

            new_reader, new_writer = self.get_reader_writer(self.db_cluster_id)
            self.assertEqual(db_reader, new_writer)
            self.assertEqual(db_writer, new_reader)


        except Exception as ex:
            self.logger.info("Test failed - " + str(ex))
            raise ex

if __name__ == '__main__':
    if len(sys.argv) > 1:
        DocumentTest.region = sys.argv.pop()
        DocumentTest.domain = sys.argv.pop()
    unittest.main()
