from boto3 import Session
from botocore.config import Config

config = Config(retries={'max_attempts': 15, 'mode': 'standard'})


def client(service_name: str, session: Session):
    """
    Creates boto3 client for given service name and boto3 session.
    :param service_name The service name to create client
    :param session The boto3 session
    """
    return session.client(service_name, config=config)


def resource(service_name: str, session: Session):
    """
    Creates boto3 resource for given service name and boto3 session.
    :param service_name The service name to create resource
    :param session The boto3 session
    """
    return session.resource(service_name, config=config)
