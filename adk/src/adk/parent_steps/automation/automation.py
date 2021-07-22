import copy
from typing import List

import yaml

from adk.src.adk.domain.data_type import DataType
from adk.src.adk.domain.input import Input
from adk.src.adk.domain.non_retriable_exception import NonRetriableException
from adk.src.adk.domain.output import Output
from adk.src.adk.parent_steps.abstract_automation_step import AbstractAutomationStep
from adk.src.adk.parent_steps.abstract_document import AbstractDocument


class Automation(AbstractAutomationStep, AbstractDocument):
    """
    This class serves both as a step (aws:executeAutomation) and an Automation document.
    You can include this Automation as you would include any other step.
    To include this as a step simply include it in the list of steps in another SSM.
    In simulation - all of the steps in the automation will be invoked during this "step"
    This class can also be used as a first class SSM Automation Document.
    When invoking this Automation as a first class SSM, you can both run the simulation and print as follows:
    The Automation can be simulated using the run_automation() function.
    It can be printed using the get_automation_yaml() function.
    See example usages in test file (same package in test 'test_automation.py')
    """
    def __init__(self, step_name: str, steps: List[AbstractAutomationStep],
                 assume_role: str, inputs: List[Input],
                 doc_outputs: List[str] = (), header: str = None, doc_name: str = None):
        AbstractAutomationStep.__init__(self, step_name)
        self._steps = self.step_validations(steps)
        self._inputs = inputs
        self._doc_outputs = self.validate_doc_outputs(doc_outputs)
        self._assume_role = self._subname(assume_role) \
            if self._subname(assume_role) not in self.get_subnames() \
            else '{{ ' + self._subname(assume_role) + ' }}'
        self._header = header
        self._doc_name = doc_name if doc_name else step_name
        AbstractDocument.__init__(self, self._create_chain())

    def get_action(self) -> str:
        return "aws:executeAutomation"

    def get_outputs(self) -> List[Output]:
        """
        SSM aws:executeAutomation outputs a single output named... 'Output'
        You can reference that output with AutomationStepName.Output in a later step that will return a list of strings.
        The List of strings are ordered by the output specified for the automation document.
        :return:
        """
        return [Output(name='Output', output_type=DataType.StringList)]

    def get_inputs(self) -> List[str]:
        return [inp.name for inp in self._inputs]

    def get_subnames(self) -> List[str]:
        return [self._subname(inp.name) for inp in self._inputs]

    def get_inputs_by_subname(self) -> dict:
        return dict((self._subname(inp.name), inp) for inp in self._inputs)

    @staticmethod
    def _subname(inp):
        return inp.split(".", 1)[-1]

    def get_description(self) -> str:
        return 'Execute another SSM Doc: ' + self.name

    def execute_step(self, params: dict) -> dict:
        output_list = []
        doc_execution_output = self.run_automation(params)
        for output in self._doc_outputs:
            if output not in doc_execution_output.keys():
                raise NonRetriableException("Output not found in automation execution: " + output + " found "
                                            + str(doc_execution_output))
            output_list.append(doc_execution_output[output])
        return {'Output': output_list}

    def run_automation(self, params: {}) -> {}:
        params_copy = copy.deepcopy(params)
        self.insert_default_inputs(params_copy)
        self.validate_inputs(params_copy)
        self._first.invoke(params_copy)
        return params_copy

    def validate_inputs(self, params):
        required_inputs = set([inp.name for inp in self._inputs if inp.default is None])
        if not required_inputs <= params.keys():
            raise Exception('Missing inputs. Required: ' + str(required_inputs) + '; Provided: ' + str(params.keys()))
        for param in params.items():
            matched_input: [Input] = [inp for inp in self._inputs if inp.name == param[0]]
            if len(matched_input):
                inp = matched_input[0]
                if param[1] is None:
                    raise Exception("Missing input for: " + inp.name)
                if not isinstance(param[1], inp.input_type.value):
                    raise Exception("Data types do not match for input: " + inp.name + ". Received "
                                    + str(type(param[1])) + ", required type " + str(inp.input_type))
                if inp.max_items and len(param[1]) > inp.max_items:
                    raise Exception("Values for input:" + param[0] + " were " + str(param[1]) + " but max_items="
                                    + inp.max_items)
                if inp.min_items and len(param[1]) > inp.min_items:
                    raise Exception("Values for input:" + param[0] + " were " + str(param[1]) + " but min_items="
                                    + inp.min_items)
                if inp.allowed_values and param[1] not in inp.allowed_values:
                    raise Exception("Value for input:" + param[0] + " was " + param[1] + "; Allowed: "
                                    + str(inp.allowed_values))

    def get_yaml(self) -> str:
        input_payload = dict((inp, '{{ ' + inp + ' }}') for inp in self.get_subnames())
        parent_yaml = yaml.safe_load(self.to_yaml(inputs={
            'DocumentName': self.name,
            'RuntimeParameters': input_payload}))
        # Outputs for automation steps are implicitly set as Output. They may not be declared in YAML.
        parent_yaml.pop('outputs', None)
        return yaml.dump(parent_yaml, sort_keys=False)

    def get_document_yaml(self) -> str:
        ssm_steps = self.get_main_steps()

        root = {
            'description': 'SOP By Digito: ' + self.name,
            'schemaVersion': '0.3',
            'assumeRole': self._assume_role,
            'parameters': self._get_ssm_inputs()}
        if len(self._doc_outputs):
            root.update({'outputs': self._doc_outputs})
        root.update({'mainSteps': ssm_steps})
        prefix = self.header_with_comments(self._header) + "\n---\n" if self._header else ''
        return prefix + yaml.dump(root, sort_keys=False)

    def _create_chain(self):
        first_step = self._steps[0]
        previous_step = first_step
        for i in range(1, len(self._steps)):
            previous_step.then(self._steps[i])
            previous_step = self._steps[i]
        return first_step

    def _get_ssm_inputs(self):
        ssm_inputs = {}
        for inp in self._inputs:
            nested = {
                'type': inp.input_type.name,
                'description': inp.description
            }
            if inp.default is not None:
                nested.update({'default': inp.default})
            if inp.allowed_values is not None:
                nested.update({'allowedValues': inp.allowed_values})
            if inp.min_items:
                nested.update({'minItems': inp.min_items})
            if inp.max_items:
                nested.update({'maxItems': inp.max_items})
            ssm_inputs.update({
                inp.name: nested
            })
        return ssm_inputs

    def step_validations(self, steps):
        if len(steps) == 0:
            raise Exception('Steps may not be empty. There must be at least one step provided.')
        step_names = [step.name for step in steps]
        if len(step_names) != len(set(step_names)):
            raise Exception('Step names must be unique in an automation doc, but found repeats: ' + str(step_names))
        return steps

    def validate_doc_outputs(self, doc_outputs):
        for doc_output in doc_outputs:
            if "." not in doc_output:
                raise Exception("doc_outputs must be specified as StepName.Output but was " + doc_output)
            step_name, output = doc_output.split(".", 1)
            self.validate_doc_output(step_name, output)
        return doc_outputs

    def validate_doc_output(self, step_name, output):
        for step in self._steps:
            if step.name == step_name and output in [out.name for out in step.get_outputs()]:
                return
        raise Exception("doc_outputs must be specified as StepName.Output. Not found: " + step_name + "." + output)

    def insert_default_inputs(self, params_copy):
        for name, inp in self.get_inputs_by_subname().items():
            if name not in params_copy:
                params_copy[name] = inp.default
