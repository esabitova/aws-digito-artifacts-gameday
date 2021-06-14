import time
from typing import List, Callable

import boto3

from adk.src.adk.domain.data_type import DataType
from adk.src.adk.domain.output import Output
from adk.src.adk.parent_steps.python_step import PythonStep
from adk.src.adk.steps_util.shared import amazing_function


class SampleStep(PythonStep):

    def get_description(self) -> str:
        return "Description for the step (markdown)"

    def get_outputs(self) -> List[Output]:
        """
        Make sure that you specify "$.Payload." prefix for PythonSteps (you will get a validation failure if not)
        :return: the outputs returned as keys from the script_handler
        """
        return [
            Output("Foo", DataType.Integer, "$.Payload.Foo"),
            Output("Bar", DataType.String, "$.Payload.Bar")
        ]

    def get_inputs(self) -> list:
        """
        The inputs used in this step. Be sure to specify in Step.Output format.
        :return: inputs used in the step.
        """
        return ['Ec2DescribeInstances.InstanceType']

    def get_helper_functions(self) -> List[Callable]:
        """
        The helper functions that you call during script execution.
        If you don't declare them here you will get a failure during simulation.
        The helper_functions specified here will be included in the SSM YAML generated for the step.
        :return: helper functions used during execution
        """
        return [helper_func, amazing_function]

    @staticmethod
    def script_handler(params: dict, context) -> dict:
        """
        Implementation of script used in aws:executeScript.
        :param params: input params (will include the params requested in get_inputs())
        :param context: None. Not used (but necessary for SSM)
        :return: dict with all of the outputs declared. DO NOT include Payload.
        """
        # Do complicated things... and then...
        return helper_func(params)


def helper_func(params: dict):
    # This is a comment
    client = boto3.client('ec2')
    client.describe_instances()
    time.sleep(1)

    return {
        "Foo": 4,
        "Bar": "barVal" + params['InstanceType'] + amazing_function()
    }
