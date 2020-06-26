import boto3
import json

def get_output_from_ssm_step_execution(events, context):
    ec2 = boto3.client('ec2')
    ssm = boto3.client('ssm')

    if 'ExecutionId' not in events or 'StepName' not in events or 'ResponseField' not in events:
        raise KeyError('Requires ExecutionId, StepName and ResponseField in events')

    ssmResponse = ssm.get_automation_execution(AutomationExecutionId=events['ExecutionId'])
    print('SSM response for execution : ', ssmResponse)
    for step in ssmResponse['AutomationExecution']['StepExecutions']:
        if step['StepName'] == events['StepName']:
            responseFields = events['ResponseField'].split(',')
            output = {}
            for responseField in responseFields:
                stepOutput = step['Outputs'][responseField][0]
                output[responseField] = stepOutput

            return output

    # Could not find step name
    raise Exception('Can not find step name % in ssm execution response', events['StepName'])