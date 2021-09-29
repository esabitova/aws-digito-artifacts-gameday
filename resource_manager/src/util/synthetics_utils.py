

from boto3.session import Session
from .boto3_client_factory import client
import logging


def stop_canary_if_its_running(canary_name: str, boto3_session: Session):
    """
    Checks if the given canary in running state and stops if it is.
    :param boto3_session: The boto3 session
    :param canary_name: The canary name
    """
    synthetics_client = client("synthetics", boto3_session)
    canary = synthetics_client.get_canary(Name=canary_name)
    canary_state = canary.get('Canary', {}).get('Status', {}).get('State', '')
    logging.info(f'Canary {canary_name} is in state {canary_state}')
    if canary_state in ['RUNNING', 'STARTING']:
        logging.info(f'Stopping canary {canary_name}')
        synthetics_client.stop_canary(Name=canary_name)
        logging.info(f'Canary {canary_name} was stopped')
    else:
        logging.info(
            f'Canary {canary_name} has been already stopped or has never been started.'
            f'The current state is {canary_state}')
