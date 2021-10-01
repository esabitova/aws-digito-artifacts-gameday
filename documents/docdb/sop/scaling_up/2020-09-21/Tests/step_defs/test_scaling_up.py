import logging

import boto3
import pytest
from pytest_bdd import scenario

from documents.util.scripts.src.docdb_util import delete_list_of_instances


@scenario('../features/scaling_up_usual_case.feature',
          'Execute SSM automation document Digito-ScaleUpDocumentDBClusterSOP_2020-09-21 to scale up Amazon '
          'DocumentDB cluster')
def test_scaling_up_usual_case(teardown_new_instances):
    """
    Execute SSM automation document Digito-ScaleUpDocumentDBClusterSOP_2020-09-21 to scale up Amazon DocumentDB cluster
    """


@pytest.fixture(scope='function')
def teardown_new_instances(boto3_session, ssm_test_cache):
    yield
    if 'before' in ssm_test_cache \
            and 'DBClusterIdentifier' in ssm_test_cache['before']:
        prefix = f"{ssm_test_cache['before']['DBClusterIdentifier']}-"
        cluster_id = ssm_test_cache['before']['DBClusterIdentifier']
        logging.info(f'Deleting instances with identifiers starting with [{prefix}] from cluster [{cluster_id}]')
        docdb = boto3.client('docdb')
        paginator = docdb.get_paginator('describe_db_instances')
        page_iterator = paginator.paginate(
            Filters=[{"Name": "db-cluster-id", "Values": [ssm_test_cache['before']['DBClusterIdentifier']]}]
        )
        filtered_iterator = page_iterator.search(
            f"DBInstances[?starts_with(DBInstanceIdentifier, '{prefix}')].DBInstanceIdentifier"
        )
        delete_list_of_instances(list(filtered_iterator))
        logging.info(
            f'Completed deleting instances with identifiers starting with "{prefix}" from cluster [{cluster_id}]'
        )
    else:
        logging.info('Skipping removal of new instances from cluster')
