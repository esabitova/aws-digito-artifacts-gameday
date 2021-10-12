import boto3
from botocore.config import Config
import logging

from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def check_required_params(required_params, events):
    for key in required_params:
        if key not in events:
            raise KeyError(f'Requires {key} in events')


def create_new_task_definition(events, context):
    """
    Returns a new task definition. If  `NewTaskDefinitionArn` is provided, it simply returns it.
    If no `NewTaskDefinitionArn` provided, creates a new task definition, from a one in specified service\cluster
    with new cpu and memory, if specified
    :param events: The object which contains passed parameters from SSM document
     * `NewTaskDefinitionArn` - Optional. The predefined task definition arn
     * `ServiceName` - Optional. Must be specified if `NewTaskDefinitionArn` not set. Name of ECS Service
     * `ClusterName` - Optional. Must be specified if `NewTaskDefinitionArn` not set. Name of ECS Cluster
     * `TaskDefinitionCPU` - Optional. New CPU for TaskDefinition
     * `TaskDefinitionRAM` - Optional. New RAM for TaskDefinition
    :param context: context
    :return: The arn of newly created task definition, or the NewTaskDefinitionArn if specified
    """
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    ecs_client = boto3.client('ecs', config=config)

    if 'NewTaskDefinitionArn' in events and events['NewTaskDefinitionArn']:
        # describe_task_definition will raise ClientError if not such task definition exists
        ecs_client.describe_task_definition(
            taskDefinition=events['NewTaskDefinitionArn']
        )
        return {"TaskDefinitionArn": events['NewTaskDefinitionArn']}
    else:
        required_params = [
            'ServiceName',
            'ClusterName'
        ]
        check_required_params(required_params, events)
    services = ecs_client.describe_services(
        services=[events['ServiceName']],
        cluster=events['ClusterName']
    )
    if not services['services']:
        raise ClientError(error_response={
            "Error":
                {
                    "Code": "ServiceNotFound",
                    "Message": f"Could not find service: {events['ServiceName']}"
                }
        },
            operation_name='DescribeServices'
        )
    task_definition_arn = services['services'][0]['taskDefinition']
    task_definition = ecs_client.describe_task_definition(
        taskDefinition=task_definition_arn
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
    if 'TaskDefinitionCPU' in events and events['TaskDefinitionCPU'] > 0:
        task_definition['cpu'] = str(events['TaskDefinitionCPU'])
    if 'TaskDefinitionRAM' in events and events['TaskDefinitionRAM'] > 0:
        task_definition['memory'] = str(events['TaskDefinitionRAM'])
    response = ecs_client.register_task_definition(**task_definition)

    return {"TaskDefinitionArn": response['taskDefinition']['taskDefinitionArn']}


def update_service(events, context):
    """
    Update service with `NewTaskDefinitionArn`.
    :param events: The object which contains passed parameters from SSM document
     * `ServiceName` - Required. Name of ECS Service
     * `ClusterName` - Required. Name of ECS Cluster
     * `TaskDefinitionArn` - Optional. Name of TaskDefinition
     * `NumberOfTasks` - Optional. Number of task. If NumberOfTasks < 1 or not set, used old
     value in the service
    :param context: context
    :return: True or error
    """
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    ecs_client = boto3.client('ecs', config=config)

    service_definition = {
        "service": events['ServiceName'],
        "cluster": events['ClusterName'],
        "taskDefinition": events['TaskDefinitionArn']
    }

    number_of_task = events.get('NumberOfTasks', None)
    if number_of_task and number_of_task > 0:
        service_definition.update({
            "desiredCount": number_of_task
        })

    ecs_client.update_service(**service_definition)


def stop_selected_tasks(events, context):
    """
    Stop NumberOfTasksToStop or total number of tasks running
    if NumberOfTasksToStop is greater than the total number.
    :param events: The object which contains passed parameters from SSM document
     * `ServiceName` - Required. Name of ECS Service
     * `ClusterName` - Required. Name of ECS Cluster
     * `NumberOfTasksToStop` - Required. Number of tasks to stop
    :param context: context
    :return: True or error
    """
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    ecs_client = boto3.client('ecs', config=config)

    paginator = ecs_client.get_paginator('list_tasks')
    pages = paginator.paginate(serviceName=events['ServiceName'],
                               cluster=events['ClusterName'],
                               desiredStatus='RUNNING')

    desired_count = ecs_client.describe_services(services=[events['ServiceName']],
                                                 cluster=events['ClusterName'])["services"][0]["desiredCount"]

    percentage_of_task_to_stop = events['PercentageOfTasksToStop']
    number_of_task_to_stop = 0

    if desired_count:
        number_of_task_to_stop = round(desired_count * percentage_of_task_to_stop / 100)

    tasks_stopped = 0
    for page in pages:
        task_arns = page.get('taskArns')
        for task_arn in task_arns:
            if tasks_stopped >= number_of_task_to_stop:
                break
            ecs_client.stop_task(
                cluster=events['ClusterName'],
                task=task_arn
            )
            tasks_stopped += 1

    return True


def wait_services_stable(events, context):
    """
    Wait while service will be stable.
    :param events: The object which contains passed parameters from SSM document
     * `ServiceName` - Required. Name of ECS Service
     * `ClusterName` - Required. Name of ECS Cluster
    :param context: context
    :return: True or error
    """
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    ecs_client = boto3.client('ecs', config=config)

    cluster_name = events['ClusterName']
    service = events.get('ServiceName')

    if service:
        services = [service]
    else:
        services = []
        paginator = ecs_client.get_paginator('list_services')
        pages = paginator.paginate(cluster=cluster_name)

        for page in pages:
            service_arns = page.get('serviceArns')
            services.extend(service_arns)

    waiter = ecs_client.get_waiter('services_stable')
    waiter.wait(
        cluster=cluster_name,
        services=services,
        WaiterConfig={
            'Delay': 15,
            'MaxAttempts': 20
        }
    )
    return True
