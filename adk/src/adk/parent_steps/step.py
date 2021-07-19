import abc
import inspect
import json
import re
from typing import List, Dict, Optional

import yaml
import jsonpath_ng

from adk.src.adk.domain.output import Output


class Step(object):
    """
    Step parent class. All steps inherit from this.
    This class employed Chain of Responsibility design-pattern.
    Each step does its own execution and passes the execution chain to the next step which is declared in "then()"
    DO NOT REUSE INSTANCES. They are not meant to be Singletons. A new instance should be used in each Ssm automation.
    If you want to reuse a step in multiple Ssm automations, simply create another (new) instance.
    Feel free to subclass this or any of the other available parent_steps.
    """

    DEFAULT_TIMEOUT = 3600
    DEFAULT_MAX_ATTEMPTS = 1

    def __init__(self, name: str):
        self._next_step: Optional[Step] = None
        if not name:
            raise Exception("Must provide name")
        self.name = name
        if not self.name.replace("_", "").isalnum():
            raise Exception("Name must contain only alphanumeric or ['_'], but was: " + self.name)
        if len(self.name) < 3 or len(self.name) > 128:
            raise Exception("Name must be in size range 3 to 128 but was: " + self.name)
        self._max_attempts = Step.DEFAULT_MAX_ATTEMPTS
        self._timeout_seconds = Step.DEFAULT_TIMEOUT
        self._is_end = False
        self._on_failure = None
        self._on_cancel = None
        yaml.add_representer(str, str_presenter)

    @abc.abstractmethod
    def get_outputs(self) -> List[Output]:
        """
        Output that will be returned from the execution WITHOUT prefix of step name.
        Example: [Output("MyOutput", DataType.Integer)]
        Notice that MyOutput is NOT prefixed with the name of the step.
        May be an empty list of []
        :return: the outputs that you will return in the execution
        """
        return []

    @abc.abstractmethod
    def get_inputs(self) -> List[str]:
        """
        List of inputs INCLUDING the step prefix.
        As is the custom with SSM docs, initial inputs that are provided to the SSM are not prefixed with anything.
        Example ['StepName.SomeOutput', 'InitialSsmInput']
        :return: the inputs that are required for this step to execute
        """
        return []

    @abc.abstractmethod
    def get_description(self) -> str:
        """
        Description for this step in Markdown format.
        An empty string is acceptable in which case this entry is omitted from the SSM.
        However, it is recommended that you provide a meaningful description for each step.
        :return: A description for this step
        """
        return ''

    @staticmethod
    @abc.abstractmethod
    def execute_step(params: dict) -> dict:
        """
        The python code that will execute for this step.
        If the implementation DOES NOT use python, this should perform the exact same behavior as the SSM step.
        For example, the aws:executeAwsApi logic should be mimicked in this python code.
        This function must return a dictionary with a key corresponding to each output that was declared to be exported.
        The outputs DO NOT contain the step name prefix.
        Example output: {'MyOutput': 5} which corresponds to the above declared outputs.
        :param params: the input params contain all of the previously outputted variables and the initial ssm inputs.
        :return: a dict mapping each output declared in 'get_outputs()' to their value as determined by this function.
        """
        return {}

    @abc.abstractmethod
    def get_yaml(self) -> str:
        """
        Generates the yaml for the given step.
        The yaml returned should have keys of "name", "action", "inputs", etc.
        :return: the yaml to be used in the ssm.
        """
        return ''

    @abc.abstractmethod
    def get_action(self) -> str:
        """
        The action of this step. Usually starts with 'aws:'
        Examples include aws:executeScript
        :return: the action including the aws: prefix
        """
        return ''

    @abc.abstractmethod
    def invoke(self, params: dict):
        pass

    def _validate_input(self, params):
        if not set(self.get_inputs()) <= params.keys():
            raise Exception("Inputs were not available for step " + self.name + ". Required " + str(self.get_inputs())
                            + ' yet the inputs provided were: ' + json.dumps(params, indent=4))

    def then(self, next_step: 'Step'):
        self._next_step = next_step
        return next_step

    def get_next_step(self):
        return self._next_step

    @abc.abstractmethod
    def to_yaml(self, inputs: Dict[str, any]) -> str:
        return ''

    def get_value_from_json(self, json_response, selector: str, identifier: str):
        value = jsonpath_ng.parse(selector).find(json_response)
        if not value:
            raise Exception('Could not find value of ' + self.name + ':' + identifier + ' selector ' + selector
                            + ' in response: ' + str(json_response) + '\nfile://' + inspect.getfile(self.__class__))
        return value[0].value

    def validations(self):
        pass

    def on_failure(self, on_failure: 'Step'):
        self._on_failure = on_failure
        return self

    @classmethod
    def replace_variables(cls, input_with_variables: str, replacement_params: {}):
        variables = re.findall('{{.*?}}', input_with_variables)
        for var in variables:
            replacement = replacement_params.get(var[2: -2].strip())
            if replacement is None:
                raise Exception('Input required but not found: ' + var)
            if type(replacement) is str:
                input_with_variables = input_with_variables.replace(var, replacement)
            elif type(replacement) is int:
                input_with_variables = input_with_variables.replace('\'' + var + '\'', str(replacement))
                input_with_variables = input_with_variables.replace('"' + var + '"', str(replacement))
            elif isinstance(replacement, list):
                input_with_variables = input_with_variables.replace(var, json.dumps(replacement))
                input_with_variables = input_with_variables.replace(var, json.dumps(replacement))
            else:
                raise Exception('Unsupported data type ' + str(type(replacement)) + " for " + str(replacement))
        return input_with_variables


def str_presenter(dumper, data):
    if len(data.splitlines()) > 1:  # check for multiline string
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)
