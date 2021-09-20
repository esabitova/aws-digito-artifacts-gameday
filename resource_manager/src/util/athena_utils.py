import logging
import time


def wait_for_query_execution(query_execution_id, athena_client, delay_sec, wait_sec):
    iteration = 1
    elapsed = 0
    while elapsed < wait_sec:
        start = time.time()
        response = athena_client.get_query_execution(
            QueryExecutionId=query_execution_id
        )
        current_state = response['QueryExecution']['Status']['State']
        previous_state = None
        if current_state != previous_state:
            logging.info(f'#{iteration}; Query execution is {current_state} '
                         f'Elapsed: {elapsed} sec;')
        if current_state == 'SUCCEEDED' or current_state == 'FAILED' or current_state == 'CANCELLED':
            return
        time.sleep(delay_sec)
        end = time.time()
        elapsed += (end - start)
        iteration += 1
