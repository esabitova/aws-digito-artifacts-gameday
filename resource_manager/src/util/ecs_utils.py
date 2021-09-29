import time
import logging

from boto3 import Session
from botocore.exceptions import ClientError

from .boto3_client_factory import client

logger = logging.getLogger(__name__)


def create_new_task_def(td_arn: str, session: Session) -> str:
    """
    Copies a task definition from a provided task definition arn
    :param td_arn: a task definition arn to copy
    :param session: a boto3 session
    :return: String - task definition arn of new task definition
    """
    td_name = td_arn.split('/')[1].split(':')[0]
    ecs_client = client('ecs', session)
    task_definition = ecs_client.describe_task_definition(
        taskDefinition=td_arn
    )['taskDefinition']
    for key in [
        'taskDefinitionArn',
        'revision',
        'status',
        'registeredAt',
        'registeredBy',
        'compatibilities',
        'requiresAttributes'
    ]:
        task_definition.pop(key)
    task_definition['family'] = f'new-{td_name}'
    task_definition['containerDefinitions'][0]['name'] = f'new-{td_name}'
    resp = ecs_client.register_task_definition(**task_definition)
    return resp["taskDefinition"]["taskDefinitionArn"]


def check_td_exits(td_arn: str, session: Session) -> bool:
    """
    checks that a task definition exists
    :param td_arn: a task definition arn
    :param session: a boto3 session
    :return: Boolean - True if task definition exists and ACTIVE, False if doesn't exist or INACTIVE
    """
    ecs_client = client('ecs', session)
    try:
        resp = ecs_client.describe_task_definition(taskDefinition=td_arn)
        if resp['taskDefinition']['status'] == 'INACTIVE':
            logger.info(f'Task Definition {td_arn} does not exist')
            return False
        else:
            logger.info(f'Task Definition {td_arn} exists')
            return True
    except ClientError as err:
        if err.response['Error']['Code'] == 'ClientException' and \
                "The specified task definition does not exist" in err.response['Error']['Message']:
            logger.info(f'Task Definition {td_arn} does not exist')
        return False


def delete_task_definition(td_arn: str,
                           service_name: str,
                           cluster_name: str,
                           old_td_arn: str,
                           wait_sec: int,
                           delay_sec: int,
                           session: Session) -> None:
    """
    Deletes task definition and replaces a task definition of a service with a provided task definition
    :param td_arn: task definition to delete
    :param service_name: service name for which we need to change task definition
    :param cluster_name: cluster name in which service_name is running
    :param old_td_arn: task definition to set for service_name
    :param wait_sec: how much to wait for deletion in seconds
    :param delay_sec: how frequently to check that task definition is already deleted
    :param session: a boto3 session
    :return: None
    """
    delete_td_and_wait(td_arn=td_arn,
                       wait_sec=int(wait_sec),
                       delay_sec=int(delay_sec),
                       session=session)
    logging.info(f"Setting Service {service_name} "
                 f"from cluster {cluster_name} "
                 f"back to task definition {old_td_arn}")
    ecs_client = client('ecs', session)
    ecs_client.update_service(
        service=service_name,
        cluster=cluster_name,
        taskDefinition=old_td_arn
    )


def delete_td_and_wait(td_arn: str,
                       wait_sec: int,
                       delay_sec: int,
                       session: Session) -> None:
    """
    Deletes task definition by its arn
    :param td_arn: task definition to delete
    :param wait_sec: how much to wait for deletion in seconds
    :param delay_sec: how frequently to check that task definition is already deleted
    :param session: a boto3 session
    :return: raises TimeoutError if td is not deleted after wait_sec
    """
    logging.info(f"Deleting Task Definition: {td_arn} "
                 f"waiting for {wait_sec} "
                 f"checking every {delay_sec} secs")
    exists = check_td_exits(td_arn, session)
    if exists:
        ecs_client = client('ecs', session)
        ecs_client.deregister_task_definition(taskDefinition=td_arn)
        start = time.time()
        elapsed = 0
        while elapsed < wait_sec:
            exists = check_td_exits(td_arn, session)
            if not exists:
                logger.info(f'The task definition `{td_arn}` has been deleted')
                return

            end = time.time()
            elapsed = end - start
            time.sleep(delay_sec)

        raise TimeoutError(f'Timeout of waiting the task definition deleted. TD arn: `{td_arn}`')


def get_amount_of_tasks(cluster_name: str,
                        service_name: str,
                        session: Session) -> int:
    """
    Get amount of tasks by cluster_name and service_name.
    :param service_name: service name for which we need to get amount of tasks
    :param cluster_name: cluster name in which we need to get amount of tasks
    :param session: a boto3 session
    :return: int - amount of tasks
    """
    ecs_client = client('ecs', session)
    amount_of_task = len(ecs_client.list_tasks(cluster=cluster_name,
                                               serviceName=service_name)['taskArns'])
    return amount_of_task


def get_container_definitions(td_arn: str,
                              session: Session) -> dict:
    """
    Get container definitions by td_arn.
    :param td_arn: task definition to delete
    :param session: a boto3 session
    :return: dict - container definitions
    """
    ecs_client = client('ecs', session)

    container_definitions = ecs_client. \
        describe_task_definition(taskDefinition=td_arn)["taskDefinition"]["containerDefinitions"][0]
    return container_definitions


def wait_services_stable(cluster_name: str,
                         service_name: str,
                         session: Session):
    """
    Wait while service will be stable.
    :param service_name: service name for which we need to wait
    :param cluster_name: cluster name in which we need to wait
    :param session: a boto3 session
    """
    ecs_client = client('ecs', session)

    waiter = ecs_client.get_waiter('services_stable')
    waiter.wait(
        cluster=cluster_name,
        services=[service_name],
        WaiterConfig={
            'Delay': 15,
            'MaxAttempts': 20
        }
    )


def get_number_of_nodes_in_status(session: Session, ecs_cluster: str, node_status: str) -> int:
    ecs_client = client('ecs', session)

    describe_cluster = ecs_client.describe_clusters(
        clusters=[ecs_cluster]
    )
    if not describe_cluster['clusters']:
        raise ClientError(
            error_response={
                "Error":
                    {
                        "Code": "ClusterNotFound",
                        "Message": f"Could not find cluster: {ecs_cluster}"
                    }
            },
            operation_name='ListContainerInstances'
        )
    paginator = ecs_client.get_paginator('list_container_instances')
    page_iterator = paginator.paginate(
        cluster=ecs_cluster,
        status=node_status
    )
    amount_of_nodes = 0
    for page in page_iterator:
        amount_of_nodes = amount_of_nodes + len(page['containerInstanceArns'])
    return amount_of_nodes
