import logging
import time
from boto3 import Session
from .boto3_client_factory import client
import resource_manager.src.constants as constants


def reboot_instance(session: Session, instance_id: str):
    """
    Uses EC2 to reboot a client instance
    """
    ec2 = client('ec2', session)
    ec2.reboot_instances(InstanceIds=[instance_id])


def modify_ec2_instance_type(session: Session, instance_id: str, instance_type: str,
                             logger: logging.Logger = logging.getLogger()):
    """
    Modify EC2 instance type to given instance type and instance id.
    :param session: The boto3 session.
    :param instance_id: The EC2 instance id.
    :param instance_type: The EC2 instance type.
    :param logger: The logger.
    """
    ec2 = client('ec2', session)
    ec2.stop_instances(InstanceIds=[instance_id])
    wait_for_ec2_state(session, instance_id, 'stopped', logger)
    ec2.modify_instance_attribute(Attribute='instanceType', InstanceId=instance_id, Value=instance_type)
    ec2.start_instances(InstanceIds=[instance_id])
    wait_for_ec2_state(session, instance_id, 'running', logger)


def wait_for_ec2_state(session, instance_id: str, state: str, logger: logging.Logger = logging.getLogger()):
    """
    Wait for EC2 instance to be switched to given state.
    :param session: The boto3 session.
    :param instance_id: The EC2 instance id.
    :param state: The EC2 instance state to wait for.
    :param logger: The logger.
    """
    ec2_client = client('ec2', session)
    instance_state = ec2_client.describe_instance_status(InstanceIds=[instance_id], IncludeAllInstances=True)
    instance_state_name = instance_state['InstanceStatuses'][0]['InstanceState']['Name']

    time_elapsed_secs = 0
    while instance_state_name != state:
        if time_elapsed_secs < constants.wait_time_out_secs:
            instance_state = ec2_client.describe_instance_status(InstanceIds=[instance_id], IncludeAllInstances=True)
            instance_state_name = instance_state['InstanceStatuses'][0]['InstanceState']['Name']
            logger.info(
                f'Waiting [{constants.sleep_time_secs}] seconds for EC2 instance '
                f'[{instance_id}] to be in state [{state}].')
            time.sleep(constants.sleep_time_secs)
            time_elapsed_secs = time_elapsed_secs + constants.sleep_time_secs
        else:
            raise Exception(
                f'Waiting for EC2 instance [{instance_id}] to be in state [{state}] '
                f'timed out after [{constants.wait_time_out_secs}].')
