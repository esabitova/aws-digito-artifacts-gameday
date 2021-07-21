import boto3
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

    ecs_client = boto3.client('ecs')

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
        task_definition['cpu'] = events['TaskDefinitionCPU']
    if 'TaskDefinitionRAM' in events and events['TaskDefinitionRAM'] > 0:
        task_definition['memory'] = events['TaskDefinitionRAM']
    response = ecs_client.register_task_definition(**task_definition)

    return {"TaskDefinitionArn": response['taskDefinition']['taskDefinitionArn']}
