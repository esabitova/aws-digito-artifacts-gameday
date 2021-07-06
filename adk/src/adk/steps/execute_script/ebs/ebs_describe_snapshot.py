from typing import List, Callable

import boto3

from adk.src.adk.domain.data_type import DataType
from adk.src.adk.domain.output import Output
from adk.src.adk.parent_steps.python_step import PythonStep


class EbsDescribeSnapshot(PythonStep):
    def get_helper_functions(self) -> List[Callable]:
        return []

    @staticmethod
    def script_handler(params: dict, context):
        response = boto3.client('ec2').describe_snapshots(Filters=[{
            'Name': 'snapshot-id',
            'Values': [params['EBSSnapshotIdentifier']]}])
        return {
            'VolumeId': response['Snapshots'][0]['VolumeId'],
            'State': response['Snapshots'][0]['State'],
            'RecoveryPoint': response['Snapshots'][0]['StartTime'].isoformat()
        }

    def get_outputs(self) -> List[Output]:
        return [
            Output('VolumeId', DataType.String, '$.Payload.VolumeId'),
            Output('State', DataType.String, '$.Payload.State'),
            Output('RecoveryPoint', DataType.String, '$.Payload.RecoveryPoint')
        ]

    def get_inputs(self) -> List[str]:
        return ['EBSSnapshotIdentifier']

    def get_description(self) -> str:
        return 'Get current snapshot information, validate that the state is "completed" by calling ' \
               '[DescribeSnapshot](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeSnapshots.html)'
