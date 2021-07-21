import json
import re
from typing import Dict, List

import boto3

from adk.src.adk.domain.output import Output
from adk.src.adk.parent_steps.abstract_automation_step import AbstractAutomationStep


class AwsApiStep(AbstractAutomationStep):
    """
    Sub-class this abstract class to implement an "aws:executeAwsApi"
    """

    def __init__(self, name: str, description: str, service: str, camel_case_api: str,
                 api_params: Dict, outputs: List[Output], python_api: str = None):
        super().__init__(name)
        self._description = description
        self._service = service
        self._camel_case_api = camel_case_api
        self._api_params = api_params
        self._outputs = outputs
        self._python_api = python_api

    def get_description(self) -> str:
        return self._description

    def get_outputs(self) -> List[Output]:
        return self._outputs

    def get_service(self) -> str:
        """
        :return: Service on which to invoke the api. (ex: 'ec2' or 'autoscaling')
        """
        return self._service

    def get_python_api(self) -> str:
        """
        :return: This is the underscore_api that is used by SSM (ex: 'describe_instances')
        """
        return self._python_api if self._python_api\
            else re.sub(r'(?<!^)(?=[A-Z])', '_', self.get_camel_case_api()).lower()

    def get_camel_case_api(self) -> str:
        """
        :return: This is the CamelCase api that is used by SSM (ex: 'DescribeInstances')
        """
        return self._camel_case_api

    def get_api_params(self) -> Dict:
        """
        These are the inputs as a python dict. Example
        {
            'Filters': [{
                'Name': 'instance-id',
                'Values': ['{{ InstanceId }}']
            }]
        }
        """
        return self._api_params

    def get_action(self) -> str:
        return "aws:executeAwsApi"

    def get_inputs(self) -> list:
        return [var[2:-2].strip() for var in re.findall('{{.*?}}', json.dumps(self.get_api_params()))]

    def execute_step(self, params: dict) -> dict:
        client = boto3.client(self.get_service())
        api_params = json.dumps(self.get_api_params())
        api_params = self.replace_variables(api_params, params)
        return getattr(client, self.get_python_api())(**json.loads(api_params))

    def get_yaml(self):
        yaml_inputs = {**{'Service': self.get_service(), 'Api': self.get_camel_case_api()}, **self.get_api_params()}
        return self.to_yaml(inputs=yaml_inputs)
