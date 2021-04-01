import boto3
import json


def get_output_from_ssm_step_execution(events, context):
    print('Creating ssm client')
    print(events)
    ssm = boto3.client('ssm')

    if 'ExecutionId' not in events or 'StepName' not in events or 'ResponseField' not in events:
        raise KeyError('Requires ExecutionId, StepName and ResponseField in events')

    print('Fetching SSM response for execution')
    ssm_response = ssm.get_automation_execution(AutomationExecutionId=events['ExecutionId'])
    print('SSM response for execution : ', ssm_response)
    for step in ssm_response['AutomationExecution']['StepExecutions']:
        if step['StepName'] == events['StepName']:
            responseFields = events['ResponseField'].split(',')
            output = {}
            for responseField in responseFields:
                stepOutput = step['Outputs'][responseField][0]
                output[responseField] = stepOutput

            return output

    # Could not find step name
    raise Exception('Can not find step name % in ssm execution response', events['StepName'])


def get_inputs_from_ssm_step_execution(events, context):
    print('Creating ssm client')
    print(events)
    ssm = boto3.client('ssm')

    if 'ExecutionId' not in events or 'StepName' not in events or 'ResponseField' not in events:
        raise KeyError('Requires ExecutionId, StepName and ResponseField in events')

    print('Fetching SSM response for execution')
    ssm_response = ssm.get_automation_execution(AutomationExecutionId=events['ExecutionId'])
    print('SSM response for execution : ', ssm_response)
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


def get_step_durations(events, context):
    ssm = boto3.client('ssm')

    if 'ExecutionId' not in events or 'StepName' not in events:
        raise KeyError('Requires ExecutionId, StepName in events')

    ssm_response = ssm.get_automation_execution(AutomationExecutionId=events['ExecutionId'])
    print('SSM response for execution : ', ssm_response)

    step_names = events['StepName'].split(',')
    duration = 0
    for step in ssm_response['AutomationExecution']['StepExecutions']:
        if step['StepName'] in step_names:
            duration += (step['ExecutionEndTime'] - step['ExecutionStartTime']).seconds

    if duration > 0:
        output = {}
        output['duration'] = str(round(duration))
        return output

    raise Exception('Can not find step name % in ssm execution response', events['StepName'])


def cancel_command_execution(events, context):
    if 'ExecutionId' not in events or 'InstanceIds' not in events or 'StepName' not in events:
        raise KeyError('Requires DocumentName, InstanceIds, Parameters in events')
    events['ResponseField'] = 'CommandId'
    command_id = get_output_from_ssm_step_execution(events, context)[events['ResponseField']]

    ssm = boto3.client('ssm')
    ssm.cancel_command(
        CommandId=command_id,
        InstanceIds=events['InstanceIds']
    )


def run_command_document_async(events, context):
    if 'DocumentName' not in events or 'InstanceIds' not in events:
        raise KeyError('Requires DocumentName, InstanceIds, Parameters in events')

    params = json.loads(events['DocumentParameters']) if 'DocumentParameters' in events else {}
    ssm = boto3.client('ssm')
    response = ssm.send_command(
        InstanceIds=events['InstanceIds'],
        DocumentName=events['DocumentName'],
        Parameters=params
    )
    return {'CommandId': response['Command']['CommandId']}


def get_inputs_from_ssm_execution(events, context):
    print('Creating ssm client')
    print(events)
    ssm = boto3.client('ssm')

    if 'ExecutionId' not in events:
        raise KeyError('Requires ExecutionId')

    ssm_response = ssm.get_automation_execution(AutomationExecutionId=events['ExecutionId'])
    ssm_response_parameters = ssm_response['AutomationExecution']['Parameters']
    output = {}
    for parameter in ssm_response_parameters:
        output[parameter] = ssm_response_parameters[parameter][0]
    return output
