import yaml
import abc

from adk.src.adk.parent_steps.step import Step


class AbstractDocument(object):

    def __init__(self, first: Step):
        self._first = first

    def get_main_steps(self):
        current_step = self._first
        ssm_steps = [yaml.safe_load(current_step.get_yaml())]
        current_step.validations()
        while current_step.get_next_step():
            current_step = current_step.get_next_step()
            current_step.validations()
            ssm_steps.append(yaml.safe_load(current_step.get_yaml()))
        return ssm_steps

    @abc.abstractmethod
    def get_document_yaml(self) -> str:
        pass
