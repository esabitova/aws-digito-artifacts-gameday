import abc
import inspect
import json
import time
from typing import List, Dict, Optional

import yaml
import jsonpath_ng

from adk.src.adk.domain.cancellation_exception import CancellationException
from adk.src.adk.domain.non_retriable_exception import NonRetriableException
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

    def invoke(self, params: dict):
        params.setdefault("python_simulation_steps", [])
        params["python_simulation_steps"].append(self.name)
        self.validations()
        self._invoke_with_fallback(params)

    def _invoke_with_fallback(self, params):
        try:
            response_dict = self._invoke_with_retries(params)
            params.update(response_dict)
            if self._next_step:
                self._next_step.invoke(params)
        except CancellationException as exc:
            if self._on_cancel:
                print('Step failed: ' + self.name + ". Executing onCancel step " + self._on_cancel.name)
                return self._on_cancel.invoke(params)
            else:
                raise exc
        except Exception as exc:
            if self._on_failure:
                print('Step failed: ' + self.name + ". Executing onFailure step " + self._on_failure.name)
                return self._on_failure.invoke(params)
            else:
                raise exc

    def _invoke_with_retries(self, params):
        exception = None
        for i in range(self._max_attempts):
            try:
                print('Invoking step ' + self.name + ': attempt ' + str(i))
                response_dict = self._try_invoke(params)
                return response_dict
            except NonRetriableException as exc:
                raise exc
            except Exception as exc:
                exception = exc
        raise exception

    def _try_invoke(self, params):
        start = time.time()
        self._validate_input(params)
        response = self.execute_step({k.split('.')[-1]: v for k, v in params.items()})
        response_dict = self._get_selected_response(response)
        self._check_execution_time(start)
        return response_dict

    def _check_execution_time(self, start):
        execution_time = time.time() - start
        if execution_time > self._timeout_seconds:
            raise Exception("Execution time exceeded timeout: timeout set to " + str(
                self._timeout_seconds) + " but took " + str(execution_time))

    def _get_selected_response(self, response):
        response_dict = {}
        for declared_output in self.get_outputs():
            val = self.get_value_from_json(response, declared_output.selector, declared_output.name)
            if not issubclass(type(val), declared_output.output_type.value):
                raise Exception("Type received was not what was expected for output: " + self.name + ":"
                                + declared_output.name + ". Type expected: " + declared_output.output_type.name
                                + " but received " + str(val))
            response_dict[self.name + '.' + declared_output.name] = val
        return response_dict

    def _validate_input(self, params):
        if not set(self.get_inputs()) <= params.keys():
            raise Exception("Inputs were not available for step " + self.name + ". Required " + str(self.get_inputs())
                            + ' yet the inputs provided were: ' + json.dumps(params, indent=4))

    def then(self, next_step: 'Step'):
        self._next_step = next_step
        return next_step

    def get_next_step(self):
        return self._next_step

    def to_yaml(self, inputs: Dict[str, any]) -> str:
        formatted_outputs = [
            {'Name': out.name, 'Selector': out.selector, 'Type': out.output_type.name} for out in self.get_outputs()]
        ssm_def = {}
        if self.get_description():
            ssm_def.update({'description': self.get_description()})
        ssm_def.update({
            'name': self.name,
            'action': self.get_action(),
            'inputs': inputs,
        })
        if len(self.get_outputs()):
            ssm_def.update({'outputs': formatted_outputs})
        if self._is_end:
            ssm_def.update({'isEnd': True})
        if self._max_attempts != Step.DEFAULT_MAX_ATTEMPTS:
            ssm_def.update({'maxAttempts': self._max_attempts})
        if self._timeout_seconds != Step.DEFAULT_TIMEOUT:
            ssm_def.update({'timeoutSeconds': self._timeout_seconds})
        if self._on_cancel:
            ssm_def.update({'onCancel': 'step:' + self._on_cancel.name})
        if self._on_failure:
            ssm_def.update({'onFailure': 'step:' + self._on_failure.name})

        return yaml.dump(ssm_def, sort_keys=False)

    def get_value_from_json(self, json_response, selector: str, identifier: str):
        value = jsonpath_ng.parse(selector).find(json_response)
        if not value:
            raise Exception('Could not find value of ' + self.name + ':' + identifier + ' selector ' + selector
                            + ' in response: ' + str(json_response) + '\nfile://' + inspect.getfile(self.__class__))
        return value[0].value

    def validations(self):
        if not self.name.replace("_", "").isalnum():
            raise Exception("Name must contain only alphanumeric or '_', but was: " + self.name)
        if len(self.name) < 3 or len(self.name) > 128:
            raise Exception("Name must be in size range 3 to 128 but was: " + self.name)

    def max_attempts(self, max_attempts: int):
        self._max_attempts = max_attempts
        return self

    def timeout_seconds(self, timeout_seconds: int):
        self._timeout_seconds = timeout_seconds
        return self

    def is_end(self, is_end: bool):
        self._is_end = is_end
        return self

    def on_failure(self, on_failure: 'Step'):
        self._on_failure = on_failure
        return self

    def on_cancel(self, on_cancel: 'Step'):
        self._on_cancel = on_cancel
        return self


def str_presenter(dumper, data):
    if len(data.splitlines()) > 1:  # check for multiline string
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)
