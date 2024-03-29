import json
import boto3
from botocore.config import Config


def get_output_from_ssm_step_execution(events, context):
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    ssm = boto3.client('ssm', config=config)

    if 'ExecutionId' not in events or 'StepName' not in events or 'ResponseField' not in events:
        raise KeyError('Requires ExecutionId, StepName and ResponseField in events')

    ssm_response = ssm.get_automation_execution(AutomationExecutionId=events['ExecutionId'])
    for step in ssm_response['AutomationExecution']['StepExecutions']:
        if step['StepName'] == events['StepName']:
            response_fields = events['ResponseField'].split(',')
            output = {}
            for response_field in response_fields:
                if response_field in step['Outputs']:
                    output[response_field] = step['Outputs'][response_field]
                else:
                    """
                    By default SSM ignores empty values when encodes API outputs to JSON. It may result in
                    a situation when an empty value is a valid value but step output completely misses it.
                    Usually happens with SQS queue policies, default policy is returned by API as an empty value
                    and executeApi step output ignores it. As a result, further steps in rollback execution will fail.
                    Instead of ignoring this value we should use a default empty value in rollback, i.e. empty string
                    represents a default sqs policy
                    """
                    output[response_field] = ['']
            return output

    # Could not find step name
    raise Exception('Can not find step name % in ssm execution response', events['StepName'])


def get_inputs_from_ssm_step_execution(events, context):
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    ssm = boto3.client('ssm', config=config)

    if 'ExecutionId' not in events or 'StepName' not in events or 'ResponseField' not in events:
        raise KeyError('Requires ExecutionId, StepName and ResponseField in events')

    ssm_response = ssm.get_automation_execution(AutomationExecutionId=events['ExecutionId'])
    for step in ssm_response['AutomationExecution']['StepExecutions']:
        if step['StepName'] == events['StepName']:
            response_fields = events['ResponseField'].split(',')
            output = {}
            for response_field in response_fields:
                step_output = step['Inputs'][response_field]
                output[response_field] = json.loads(step_output)
            return output

    # Could not find step name
    raise Exception('Can not find step name % in ssm execution response', events['StepName'])


def get_inputs_from_input_payload_ssm_step_execution(events, context):
    if 'ExecutionId' not in events or 'StepName' not in events or 'InputPayloadField' not in events:
        raise KeyError('Requires ExecutionId, StepName and InputPayloadField in events')
    events['ResponseField'] = 'InputPayload'
    payload = get_inputs_from_ssm_step_execution(events=events,
                                                 context=context)
    field = events['InputPayloadField']
    return {
        field: payload['InputPayload'][field]
    }


def get_step_durations(events, context):
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    ssm = boto3.client('ssm', config=config)

    if 'ExecutionId' not in events or 'StepName' not in events:
        raise KeyError('Requires ExecutionId, StepName in events')

    ssm_response = ssm.get_automation_execution(AutomationExecutionId=events['ExecutionId'])

    step_names = events['StepName'].split(',')
    duration = 0
    for step in ssm_response['AutomationExecution']['StepExecutions']:
        if step['StepName'] in step_names:
            duration += (step['ExecutionEndTime'] - step['ExecutionStartTime']).seconds

    if duration > 0:
        output = {'duration': str(round(duration))}
        return output

    raise Exception('Can not find step name % in ssm execution response', events['StepName'])


def cancel_command_execution(events, context):
    if 'ExecutionId' not in events or 'InstanceIds' not in events or 'StepName' not in events:
        raise KeyError('Requires DocumentName, InstanceIds, Parameters in events')
    events['ResponseField'] = 'CommandId'
    command_id = get_output_from_ssm_step_execution(events, context)[events['ResponseField']][0]
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    ssm = boto3.client('ssm', config=config)
    ssm.cancel_command(
        CommandId=command_id,
        InstanceIds=events['InstanceIds']
    )


def run_command_document_async(events, context):
    if 'DocumentName' not in events or 'InstanceIds' not in events:
        raise KeyError('Requires DocumentName, InstanceIds, Parameters in events')

    params = json.loads(events['DocumentParameters']) if 'DocumentParameters' in events else {}
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    ssm = boto3.client('ssm', config=config)
    response = ssm.send_command(
        InstanceIds=events['InstanceIds'],
        DocumentName=events['DocumentName'],
        Parameters=params
    )
    return {'CommandId': response['Command']['CommandId']}


def get_inputs_from_ssm_execution(events, context):
    output = {}
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    ssm = boto3.client('ssm', config=config)

    if 'ExecutionId' not in events:
        raise KeyError('Requires ExecutionId')

    if not events['ExecutionId']:
        raise KeyError('Requires not empty ExecutionId')

    response = ssm.get_automation_execution(AutomationExecutionId=events['ExecutionId'])
    response_parameters = response['AutomationExecution']['Parameters']
    # TODO DIG-853
    for parameter in response_parameters:
        output[parameter] = response_parameters[parameter]

    return output


def start_rollback_execution(events, context):
    output = {}
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    ssm = boto3.client('ssm', config=config)

    if 'ExecutionId' not in events or not events['ExecutionId']:
        raise KeyError('Requires not empty ExecutionId')

    response = ssm.get_automation_execution(AutomationExecutionId=events['ExecutionId'])

    # Get parameters for current execution and add IsRollback and PreviousExecutionId
    response_parameters = response['AutomationExecution']['Parameters']
    response_parameters['IsRollback'] = ['true']
    response_parameters['PreviousExecutionId'] = [events['ExecutionId']]

    rollback_execution_response = ssm.start_automation_execution(
        DocumentName=response['AutomationExecution']['DocumentName'],
        DocumentVersion=response['AutomationExecution']['DocumentVersion'],
        Parameters=response_parameters
    )
    output['RollbackExecutionId'] = rollback_execution_response['AutomationExecutionId']
    return output


def convert_param_types(events, context):
    """
    Use this script to convert value types from strings to specific OutputTypes
    All outputs and inputs from SSM steps received through API calls have string type regardless of their actual type
    On the other hand various AWS APIs expect params to be in types other than strings
    """
    output = {}
    params = events.get('Parameters', [])
    for param in params:
        param_name = param.get('Name')
        value = param.get('Value')
        output_type = param.get('OutputType')
        if not param_name or not output_type or 'Value' not in param:
            raise ValueError(f"Failed to get function parameters from input payload: {param}")
        if output_type not in ["Float", "Integer", "Boolean"]:
            raise ValueError(f"Incorrect OutputType in events: {output_type}")

        if output_type == 'Float':
            output[param_name] = float(value)
        if output_type == 'Integer':
            output[param_name] = int(value)
        if output_type == 'Boolean':
            output[param_name] = value.lower() == 'true'
    return output
