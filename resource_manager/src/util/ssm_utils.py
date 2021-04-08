from boto3 import Session
from datetime import datetime
from .boto3_client_factory import client, resource


def get_ssm_step_interval(session: Session, execution_id, step_name):
    """
    Returns SSM automation step execution time interval in GMT/UTC. If Step is not
    completed at the time of fetching then interval 'end time' is present.
    :param session The AWS session
    :param execution_id The SSM automation execution id
    :param step_name The SSM automation step name
    """
    ssm = client('ssm', session)
    ssm_response = ssm.get_automation_execution(AutomationExecutionId=execution_id)
    for step in ssm_response['AutomationExecution']['StepExecutions']:
        if step['StepName'] == step_name:
            start_time = step.get('ExecutionStartTime')
            if start_time is None:
                raise Exception('Automation step [{}:{}] didn`t started'.format(execution_id, step_name))
            end_time = step.get('ExecutionEndTime')
            if end_time is None:
                return (datetime.utcfromtimestamp(start_time.timestamp()), datetime.utcnow())
            return (datetime.utcfromtimestamp(start_time.timestamp()), datetime.utcfromtimestamp(end_time.timestamp()))
    raise Exception('Automation step [{}:{}] was not found.'.format(execution_id, step_name))


def get_ssm_step_status(session: Session, execution_id, step_name):
    """
    Returns SSM automation step status.
    :param session The AWS session
    :param execution_id The SSM automation execution id
    :param step_name The SSM automation step name
    """
    ssm = session.client('ssm')
    ssm_response = ssm.get_automation_execution(AutomationExecutionId=execution_id)
    for step in ssm_response['AutomationExecution']['StepExecutions']:
        if step['StepName'] == step_name:
            return step['StepStatus']
    raise Exception('Step with name [{}:{}] was not found.'.format(execution_id, step_name))
