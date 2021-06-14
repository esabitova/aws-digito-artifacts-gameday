import unittest
from typing import List, Callable

import pytest

from adk.src.adk.steps.sample_step import SampleStep
from adk.src.adk.domain.data_type import DataType
from adk.src.adk.domain.output import Output
from adk.src.adk.parent_steps.python_step import PythonStep


@pytest.mark.unit_test
class TestPauseStep(unittest.TestCase):

    def test_should_execute_python(self):
        params = {}
        MyPython().invoke(params)
        self.assertEqual(4, params['MyPython.Foo'])

    def test_should_print_yaml(self):
        python_yaml = MyPython().get_yaml()
        self.assertEqual('description: Bar\n'
                         'name: MyPython\n'
                         'action: aws:executeScript\n'
                         'inputs:\n'
                         '  Runtime: python3.6\n'
                         '  Handler: script_handler\n'
                         '  Script: |2\n'
                         '\n'
                         '\n'
                         '    def script_handler(params: dict, context) -> dict:\n'
                         '        return {\'Foo\': my_helper()}\n'
                         '\n'
                         '    def my_helper():\n'
                         '        return 4\n'
                         '  InputPayload: {}\n'
                         'outputs:\n'
                         '- Name: Foo\n'
                         '  Selector: $.Payload.Foo\n'
                         '  Type: Integer\n', python_yaml)

    def test_validations(self):
        SampleStep().validations()


class MyPython(PythonStep):
    def get_helper_functions(self) -> List[Callable]:
        return [my_helper]

    def get_outputs(self) -> List[Output]:
        return [Output(name='Foo', output_type=DataType.Integer, selector='$.Payload.Foo')]

    def get_inputs(self) -> List[str]:
        return []

    def get_description(self) -> str:
        return "Bar"

    @staticmethod
    def script_handler(params: dict, context) -> dict:
        return {'Foo': my_helper()}


def my_helper():
    return 4
