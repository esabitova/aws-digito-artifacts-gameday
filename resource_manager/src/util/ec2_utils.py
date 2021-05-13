from boto3 import Session
from .boto3_client_factory import client


def reboot_instance(session: Session, instance_id: str):
    """
    Uses EC2 to reboot a client instance
    """
    ec2 = client('ec2', session)
    ec2.reboot_instances(InstanceIds=[instance_id])
