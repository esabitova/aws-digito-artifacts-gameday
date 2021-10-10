from time import sleep
from typing import List, Callable

import boto3

from adk.src.adk.domain.output import Output
from adk.src.adk.parent_steps.automation.python_step import PythonStep


class WaitForVolumeSize(PythonStep):
    def get_helper_functions(self) -> List[Callable]:
        return []

    @staticmethod
    def script_handler(params: dict, context):
        ec2 = boto3.client('ec2')
        while True:
            response = ec2.describe_volumes(VolumeIds=[params['VolumeId']])
            if response['Volumes'][0]['Size'] == params['SizeGib']:
                return {}
            print('Sleeping for 3 seconds because received response of ' + str(response['Volumes'][0]['Size']))
            sleep(3)

    def get_outputs(self) -> List[Output]:
        return []

    def get_inputs(self) -> List[str]:
        return ['SizeGib', 'DescribeInstanceVolume.VolumeId']

    def get_description(self) -> str:
        return 'Wait until volume is updated to new value.'
