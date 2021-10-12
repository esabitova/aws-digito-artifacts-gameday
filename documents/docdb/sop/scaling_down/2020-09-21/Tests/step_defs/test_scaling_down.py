import logging
from concurrent.futures import ThreadPoolExecutor

import boto3
import pytest
from pytest_bdd import scenario

from documents.util.scripts.src.docdb_util import create_docdb_instance


@scenario('../features/scaling_down_usual_case.feature',
          'Execute SSM automation document Digito-ScaleDownDocumentDBClusterSOP_2020-09-21 to scale down Amazon '
          'DocumentDB cluster. NumberOfDBInstancesToDelete.')
def test_scaling_down_usual_case_number(teardown_recreate_instances):
    """Execute SSM automation document Digito-ScaleDownDocumentDBClusterSOP_2020-09-21"""


@scenario('../features/scaling_down_usual_case.feature',
          'Execute SSM automation document Digito-ScaleDownDocumentDBClusterSOP_2020-09-21 to scale down Amazon '
          'DocumentDB cluster. DBInstancesIdentifiersToDelete.')
def test_scaling_down_usual_case_ids(teardown_recreate_instances):
    """Execute SSM automation document Digito-ScaleDownDocumentDBClusterSOP_2020-09-21"""


@pytest.fixture(scope='function')
def teardown_recreate_instances(boto3_session, ssm_test_cache):
    yield
    if 'before' in ssm_test_cache \
            and 'DBClusterIdentifier' in ssm_test_cache['before'] \
            and 'DBInstances' in ssm_test_cache['before']:
        expected_instances = ssm_test_cache['before']['DBInstances']
        cluster_id = ssm_test_cache['before']['DBClusterIdentifier']
        docdb = boto3.client('docdb')
        actual_instances = docdb.describe_db_instances(
            Filters=[{"Name": "db-cluster-id", "Values": [cluster_id]}]
        )['DBInstances']
        actual_available_instances = [i for i in actual_instances if i['DBInstanceStatus'] == 'available']
        number_of_instances_to_create = len(expected_instances) - len(actual_available_instances)
        if number_of_instances_to_create > 0:
            logging.info(f'Creating {number_of_instances_to_create} instances in cluster [{cluster_id}]')
            with ThreadPoolExecutor(max_workers=5) as t_executor:
                for instance in expected_instances:
                    if instance['DBInstanceIdentifier'] not in actual_available_instances:
                        t_executor.submit(create_docdb_instance, instance)
            logging.info(
                f'Completed creating new instances for cluster [{cluster_id}]'
            )
        else:
            logging.info('Skipping creating of new instances')
    else:
        logging.info('Skipping creating of new instances')
