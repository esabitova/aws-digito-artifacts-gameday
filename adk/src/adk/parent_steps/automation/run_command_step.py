import copy
import json
import re
from typing import List, Dict

import boto3
import yaml

from adk.src.adk.domain.data_type import DataType
from adk.src.adk.domain.input import Input
from adk.src.adk.domain.output import Output
from adk.src.adk.parent_steps.abstract_automation_step import AbstractAutomationStep
from adk.src.adk.parent_steps.abstract_command_step import AbstractCommandStep
from adk.src.adk.parent_steps.abstract_document import AbstractDocument
from adk.src.adk.parent_steps.automation.aws_api_step import AwsApiStep
from adk.src.adk.parent_steps.automation.wait_for_resource_step import WaitForResourceStep


class RunCommandStep(AbstractAutomationStep, AbstractDocument):

    def __init__(self, name: str, steps: List[AbstractCommandStep], instance_ids_input: str,
                 command_params: Dict[Input, any], header: str = None, use_send_command: bool = True,
                 run_cmd_document_name: str = None):
        AbstractAutomationStep.__init__(self, name)
        self._steps = steps
        self._instance_ids_input = instance_ids_input
        self._command_params = command_params
        self._header = header
        self._use_send_command = use_send_command
        self._run_command_document_name = name if run_cmd_document_name is None else run_cmd_document_name
        if not self._run_command_document_name.replace("_", "").replace("-", "").replace(".", "").isalnum():
            raise Exception("Document name must be alphanumeric or ['_','-',','], but was: "
                            + self._run_command_document_name)
        AbstractDocument.__init__(self, self._create_chain())

    def _create_chain(self):
        first_step = self._steps[0]
        previous_step = first_step
        supported_platforms = set(previous_step.get_supported_platforms())
        for i in range(1, len(self._steps)):
            previous_step.then(self._steps[i])
            previous_step = self._steps[i]
            supported_platforms.intersection_update(previous_step.get_supported_platforms())
        if len(supported_platforms) == 0:
            raise Exception('No supported platforms after intersecting all steps')
        print('Supported platforms: ' + str([p.value for p in supported_platforms]))
        return first_step

    def get_outputs(self) -> List[Output]:
        return [  # Output(name='CommandId', output_type=DataType.String),
            Output(name='Status', output_type=DataType.String),
            Output(name='ResponseCode', output_type=DataType.Integer),
            # Output(name='Output', output_type=DataType.String)
        ]

    def get_document_yaml(self) -> str:
        ssm_steps = self.get_main_steps()

        root = {
            'description': 'Command Document: ' + self.name,
            'schemaVersion': '2.2',
            'parameters': self._get_ssm_inputs()}

        root.update({'mainSteps': ssm_steps})
        prefix = self.header_with_comments(self._header) + "\n---\n" if self._header else ''
        return prefix + yaml.dump(root, sort_keys=False)

    def _get_ssm_inputs(self):
        ssm_inputs = {}
        for inp in self._command_params.keys():
            nested = {
                'type': inp.input_type.name,
                'description': inp.description
            }
            if inp.default is not None:
                nested.update({'default': inp.default})
            if inp.allowed_values is not None:
                nested.update({'allowedValues': inp.allowed_values})
            ssm_inputs.update({
                inp.name: nested
            })
        return ssm_inputs

    def get_inputs(self) -> List[str]:
        required_inputs = dict([(item[0].name, item[1]) for item in self._command_params.items()
                                if item[0].default is None])
        inputs = [var[2:-2].strip() for var in re.findall('{{.*?}}', json.dumps(required_inputs))]
        inputs.append(self._instance_ids_input)
        return inputs

    def get_description(self) -> str:
        return 'Command Document: ' + self.name

    def execute_step(self, params: dict) -> dict:
        try:
            if self._use_send_command:
                client = boto3.client('ssm')
                params_copy = self.copy_and_replace_params(params)
                response = client.send_command(
                    InstanceIds=[params[self._instance_ids_input]],
                    DocumentName=self._run_command_document_name,
                    Parameters=self.format_as_str_to_list(params_copy))
                WaitForResourceStep(name="SsmCommandWaitFor", service="ssm", camel_case_api="GetCommandInvocation",
                                    api_params={'CommandId': response['Command']['CommandId'],
                                                'InstanceId': params[self._instance_ids_input]},
                                    selector='$.Status',
                                    desired_values=['Success', 'Cancelled', 'TimedOut', 'Failed']).execute_step({})
                return AwsApiStep(name="SsmCommandWaitFor", service="ssm", camel_case_api="GetCommandInvocation",
                                  api_params={'CommandId': response['Command']['CommandId'],
                                              'InstanceId': params[self._instance_ids_input]},
                                  outputs=[
                                      Output(name='Status', selector='$.Status', output_type=DataType.String),
                                      Output(name='ResponseCode', selector='$.ResponseCode',
                                             output_type=DataType.Integer)
                                  ],
                                  description="Fetch Status and Response code").execute_step({})
            else:
                self.run_document(params)
            return {'Status': 'Success',
                    'ResponseCode': 0}
        except Exception as e:
            raise Exception("Execution failed for step " + self.name) from e

    def run_document(self, params: {}) -> {}:
        params_copy = self.copy_and_replace_params(params)
        self._first.invoke(params_copy)
        return params_copy

    def copy_and_replace_params(self, params):
        params_copy = copy.deepcopy(params)
        self.insert_default_inputs(params_copy)
        # self.validate_inputs(params_copy)
        input_to_value = self.get_input_to_value()
        return json.loads(self.replace_variables(json.dumps(input_to_value), params_copy))

    def get_input_to_value(self):
        input_to_value = dict([(item[0].name, item[1]) for item in self.get_default_populated_cmd_params().items()])
        return input_to_value

    def insert_default_inputs(self, params_copy):
        for name, default in [(inp.name, inp.default) for inp in self._command_params.keys()]:
            if name not in params_copy:
                params_copy[name] = default

    def get_yaml(self) -> str:
        parent_yaml = yaml.safe_load(self.to_yaml(inputs={
            'DocumentName': self._run_command_document_name,
            'InstanceIds': ['{{ ' + self._instance_ids_input + ' }}'],
            'Parameters': dict([(i[0].name, i[1]) for i in self._command_params.items() if i[1] is not None])
        }))
        # Outputs for command steps are implicitly set as Output. They may not be declared in YAML.
        parent_yaml.pop('outputs', None)
        return yaml.dump(parent_yaml, sort_keys=False)

    def get_default_populated_cmd_params(self):
        return dict([(i[0], i[0].default if i[1] is None else i[1]) for i in self._command_params.items()])

    def get_action(self) -> str:
        return 'aws:runCommand'

    def validations(self):
        super()

    def format_as_str_to_list(self, params: dict):
        return dict([(p[0], p[1] if isinstance(p[1], list) else [str(p[1])]) for p in params.items()])
