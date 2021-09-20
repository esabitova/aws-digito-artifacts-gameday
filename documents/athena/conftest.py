from pytest_bdd import (
    given,
    parsers, when
)

from resource_manager.src.util.athena_utils import wait_for_query_execution
from resource_manager.src.util.glue_utils import wait_for_crawler_running
from resource_manager.src.util.boto3_client_factory import client
from resource_manager.src.util.common_test_utils import extract_param_value


@given(parsers.parse('run the Crawler for creating table\n{input_parameters}'))
def run_crawler(resource_pool, ssm_test_cache, boto3_session, input_parameters):
    glue_crawler_name = extract_param_value(input_parameters, "GlueCrawlerName", resource_pool, ssm_test_cache)
    glue_client = client('glue', boto3_session)
    glue_client.start_crawler(
        Name=glue_crawler_name
    )
    wait_for_crawler_running(glue_crawler_name, glue_client, 20, 300)


@when(parsers.parse('execute DML query\n{input_parameters}'))
def execute_query(resource_pool, ssm_test_cache, boto3_session, input_parameters):
    database_name = extract_param_value(input_parameters, "Database", resource_pool, ssm_test_cache)
    workgroup_name = extract_param_value(input_parameters, "AthenaWorkGroupName", resource_pool, ssm_test_cache)
    table_name = extract_param_value(input_parameters, "TableName", resource_pool, ssm_test_cache)
    s3_output_bucket = extract_param_value(input_parameters, "BucketName", resource_pool, ssm_test_cache)
    athena_client = client('athena', boto3_session)
    query = 'SELECT * FROM ' + table_name + ';'

    response = athena_client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={
            'Database': database_name,
        },
        ResultConfiguration={
            'OutputLocation': s3_output_bucket,
        },
        WorkGroup=workgroup_name
    )
    query_execution_id = response['QueryExecutionId']
    wait_for_query_execution(query_execution_id, athena_client, 2, 60)


