import logging
import time

from .boto3_client_factory import client


def wait_for_crawler_running(glue_crawler_name, boto3_session, delay_sec, wait_sec):
    """

    :param glue_crawler_name:
    :param glue_client:
    :param delay_sec:
    :param wait_sec:
    :return:
    """
    glue_client = client('glue', boto3_session)
    iteration = 1
    elapsed = 0
    previous_state = None
    while elapsed < wait_sec:
        start = time.time()
        response = glue_client.get_crawler(
            Name=glue_crawler_name
        )
        current_state = response['Crawler']['State']

        if current_state != previous_state:
            logging.info(f'#{iteration}; Crawler {glue_crawler_name} is {current_state} '
                         f'Elapsed: {elapsed} sec;')
        if current_state == "READY":
            return
        time.sleep(delay_sec)
        end = time.time()
        elapsed += (end - start)
        iteration += 1
