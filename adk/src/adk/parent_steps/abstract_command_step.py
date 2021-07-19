import abc
from typing import List, Dict

import yaml

from adk.src.adk.domain.output import Output
from adk.src.adk.domain.platform import Platform
from adk.src.adk.parent_steps.step import Step


class AbstractCommandStep(Step, abc.ABC):

    def __init__(self, name: str):
        super().__init__(name)
        self._is_finally = False
        self._mark_success_on_failure = False
        self._exit_on_success = False

    @abc.abstractmethod
    def get_supported_platforms(self: List[Platform]):
        return []

    def is_finally_step(self, is_finally: bool):
        self._is_finally = is_finally
        return self

    def on_failure(self, mark_success: bool):
        self._mark_success_on_failure = mark_success
        return self

    def on_success(self, exit_on_success: bool):
        self._exit_on_success = exit_on_success
        return self

    def get_outputs(self) -> List[Output]:
        return []

    def invoke(self, params: dict):
        print("Executing step " + self.name)
        params.setdefault("python_simulation_steps", [])
        params["python_simulation_steps"].append(self.name)
        self.validations()
        try:
            self.execute_step(params)
            self.invoke_subsequent(params)
        except Exception as e:
            print("Execution failed for step " + self.name + ": " + str(e))
            if self._mark_success_on_failure:
                print("Step " + self.name + " marked to succeed on failure. Proceeding...")
                self.invoke_subsequent(params)
            else:
                self.invoke_finally(params)
                raise Exception('Raising previously thrown exception (raised prior to finally step)') from e

    def invoke_subsequent(self, params):
        if self._exit_on_success:
            print("Exit on success enabled for current step: " + self.name)
            self.invoke_finally(params)
        elif self._next_step:
            self._next_step.invoke(params)

    def invoke_finally(self, params):
        last_step = self._get_last_step()
        if last_step != self and last_step._is_finally:
            print("Invoking finally step: " + last_step.name)
            last_step.invoke(params)
            return True
        return False

    def to_yaml(self, inputs: Dict[str, any]) -> str:
        inputs_copy = dict(inputs)
        ssm_def = {}
        if self.get_description():
            ssm_def.update({'description': self.get_description()})
        ssm_def.update({
            'name': self.name,
            'action': self.get_action(),
            'inputs': inputs,
        })
        if self._is_finally:
            inputs_copy.update({'finallyStep': True})
        if self._exit_on_success:
            inputs_copy.update({'onFailure': 'successAndExit'})
        if self._mark_success_on_failure:
            inputs_copy.update({'onSuccess': 'exit'})

        return yaml.dump(ssm_def, sort_keys=False)

    def _get_last_step(self):
        last = self
        while last.get_next_step():
            last = last.get_next_step()
        return last
