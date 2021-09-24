import logging
import time

from resource_manager.src.util.boto3_client_factory import client


def wait_for_query_execution(query_execution_id, boto3_session, delay_sec, wait_sec, expected_query_state):
    """
    Waiter for Query execution. Checks the state of the execution
    :param expected_query_state: expected query execution state: SUCCEEDED or FAILED
    :param query_execution_id: Id of the query execution
    :param boto3_session: boto3 session
    :param delay_sec: the delay in seconds between pulling attempts of execution status
    :param wait_sec: timeout in seconds on waiting for execution completion
    :return:
    """
    athena_client = client('athena', boto3_session)
    iteration = 1
    elapsed = 0
    previous_state = None
    while elapsed < wait_sec:
        start = time.time()
        response = athena_client.get_query_execution(
            QueryExecutionId=query_execution_id
        )
        current_state = response['QueryExecution']['Status']['State']

        if current_state != previous_state:
            logging.info(f'#{iteration}; Query execution is {current_state} '
                         f'Elapsed: {elapsed} sec;')
        if current_state == expected_query_state:
            return
        time.sleep(delay_sec)
        end = time.time()
        elapsed += (end - start)
        iteration += 1

    raise AssertionError(f'After {wait_sec} seconds the query execution is in {current_state} state')
