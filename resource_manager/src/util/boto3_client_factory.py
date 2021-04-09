from boto3 import Session
from botocore.config import Config

config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
clients = {}
resources = {}


def client(service_name: str, session: Session):
    """
    Creates boto3 client for given service name and boto3 session.
    :param service_name The service name to create client
    :param session The boto3 session
    """
    client = clients.get(service_name)
    if not client:
        client = session.client(service_name, config=config)
        clients[service_name] = client
    return client


def resource(service_name: str, session: Session):
    """
    Creates boto3 resource for given service name and boto3 session.
    :param service_name The service name to create resource
    :param session The boto3 session
    """
    resource = resources.get(service_name)
    if not resource:
        resource = session.resource(service_name, config=config)
        resources[service_name] = resource
    return resource
