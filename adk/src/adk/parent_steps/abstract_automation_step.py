import abc
from abc import ABC
from typing import Dict
import time
import yaml

from adk.src.adk.domain.cancellation_exception import CancellationException
from adk.src.adk.domain.non_retriable_exception import NonRetriableException
from adk.src.adk.parent_steps.step import Step

try:
    from typing import Protocol
except ImportError:
    from typing_extensions import Protocol


class AbstractAutomationStep(Step, ABC):

    def invoke(self, params: dict):
        params.setdefault("python_simulation_steps", [])
        params["python_simulation_steps"].append(self.name)
        print(f"Executing Step: ${self.name}")
        self.validations()
        self._invoke_with_fallback(params)

    def _invoke_with_fallback(self, params):
        try:
            response_dict = self._invoke_with_retries(params)
            params.update(response_dict)
            if self._next_step and not self._is_end:
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
        print("Exception occurred in step: " + self.name)
        raise exception

    def _try_invoke(self, params):
        start = time.time()
        self._validate_input(params)
        response = self.execute_step(params)
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
                                + " but received " + str(val) + "(" + str(type(val)) + ")")
            response_dict[self.name + '.' + declared_output.name] = val
        return response_dict

    def on_cancel(self, on_cancel: 'AbstractAutomationStep'):
        self._on_cancel = on_cancel
        return self

    def max_attempts(self, max_attempts: int):
        self._max_attempts = max_attempts
        return self

    def timeout_seconds(self, timeout_seconds: int):
        self._timeout_seconds = timeout_seconds
        return self

    def is_end(self, is_end: bool):
        self._is_end = is_end
        return self

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

    def resolve_step(self, _: 'AbstractAutomationStep'):
        return self

    @staticmethod
    def header_with_comments(header):
        # Prepend header line with # if it does not start with #
        return '\n'.join([line if line.strip().startswith("#") else "# " + line for line in header.split('\n')])


class ResolveByName:
    def __init__(self, step_name: str):
        self.step_name = step_name

    def resolve_step(self, step: AbstractAutomationStep) -> AbstractAutomationStep:
        iter_step = step
        while iter_step is not None:
            if iter_step.name == self.step_name:
                return iter_step
            iter_step = iter_step.get_next_step()
        raise ValueError(f"Failed to find Step with {self.step_name} "
                         f"searching forward from {step.name if step else 'None'}")


class AutomationStepReference(Protocol):
    @abc.abstractmethod
    def resolve_step(self, step: AbstractAutomationStep) -> AbstractAutomationStep:
        # pragma: no cover
        raise NotImplementedError
