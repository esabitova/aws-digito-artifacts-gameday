import abc
import inspect
import sys
from inspect import getsource
from typing import List, Callable

from adk.src.adk.domain.non_retriable_exception import NonRetriableException
from adk.src.adk.parent_steps.step import Step


class PythonStep(Step, metaclass=abc.ABCMeta):
    """
    aws:executeScript implementation
    Subclass this class to create a new Python execution step.
    The script_handler() function will be invoked during step execution.
    You may call helper methods during the execution of script_handler().
    BEWARE #1: You MUST declare every helper function call in get_helper_functions().
    Failure to declare helper functions will cause the execution to fail and will not be generated in the yaml.
    BEWARE #2: You MUST NOT reference local helper functions with a file prefix. You can accomplish this as below:
    BAD => "import steps_util.shared"... "shared.amazing_function()" <= makes reference to file prefix
    GOOD => "from steps_util.shared import amazing_function"... "amazing_function"
    The entire execution of script_handler may not use any local variables available in "self".
    """

    def __init__(self, name=None):
        super().__init__(name if name else type(self).__name__)
        self._record = True
        self._record_stack_level = 0
        self._in_execute = False

    @abc.abstractmethod
    def get_helper_functions(self) -> List[Callable]:
        """
        Must declare all of the helper functions that you use in the python script_handler call.
        Calls to helper functions will fail unless they are "granted permission" by including them in this response.
        All functions declared as helper_methods will be included in the generated yaml.
        :return: the helper methods that are used by the script_handler method
        """
        return []

    def get_action(self) -> str:
        return 'aws:executeScript'

    def invoke(self, params: dict):
        prev = sys.getprofile()
        sys.setprofile(self.validate_function_calls)
        super().invoke(params)
        sys.setprofile(prev)

    def execute_step(self, params: dict) -> dict:
        return {"Payload": self.script_handler(params, None)}

    @staticmethod
    @abc.abstractmethod
    def script_handler(params: dict, context) -> dict:
        """
        Implement python code in this function.
        This code will be used as the step execution script.
        DO NOT use self reference (it is static).
        Any helper functions must be declared in get_helper_functions()
        :param params: Outputs from previous steps are fed in via params.
        :param context: Not to be used. This is for Lambda execution only. Don't worry about it.
        :return: All the outputs that are declared must be returned as keys in the response map.
        """
        return {}

    def validate_function_calls(self, frame, event, arg, indent=[0]):
        """
        This provides a profile that will ensure that all local python calls are declared in get_helper_functions().
        The reflection in this function makes it hard to read, so here is the logic:
        1. Only record calls inside the script_handler function (between the time that it is "call"ed and "return"ed)
        2. For every function call that is in the local module (in adk):
          a. Get the function name
          b. Check if the function name is among the function names declared in get_helper_functions() (else throw)
        """
        if frame.f_code.co_name == 'script_handler':
            self._in_execute = event == 'call'
            return
        if self._in_execute:
            if event == 'call' and self.is_local_module(inspect.getmodule(frame)):
                code_name = frame.f_code.co_name
                declared_qualnames = [func.__name__ for func in self.get_helper_functions()]
                if code_name not in declared_qualnames:
                    raise NonRetriableException(
                        "Function invoked but not declared in " + type(self).__name__ + ".get_helper_functions(): "
                        + frame.f_code.co_name + "; " + "line: file://" + frame.f_code.co_filename + ":"
                        + str(frame.f_lineno))
        return self.validate_function_calls

    def is_local_module(self, module):
        return module is not None and self.__module__.split('.')[0] in module.__name__

    def get_yaml(self) -> str:
        input_payload = dict((inp.split(".", 1)[-1], '{{ ' + inp + ' }}') for inp in self.get_inputs())
        return self.to_yaml(inputs={
            'Runtime': 'python3.6',
            'Handler': 'script_handler',
            'Script': self.get_script(),
            'InputPayload': input_payload})

    def get_script(self):
        imports = self.get_required_file_imports()
        functions = self.get_functions()
        import_lines = ["import " + imp for imp in imports]
        return '\n'.join(import_lines) + "\n\n" + '\n'.join(functions)

    def get_functions(self):
        functions = [self.get_source(self.script_handler)]
        for func in self.get_helper_functions():
            functions.append(self.get_source(func))
        return functions

    @staticmethod
    def get_source(func: Callable):
        src = getsource(func)
        src_without_decorator = '\n'.join([line for line in src.split('\n') if "staticmethod" not in line])
        leading_spaces = len(src_without_decorator) - len(src_without_decorator.lstrip(' '))
        return src_without_decorator[leading_spaces:].replace('\n' + (' ' * leading_spaces), '\n')

    def validations(self):
        super().validations()
        step_yaml = self.get_yaml()
        if 'import unittest.mock' in step_yaml:
            raise Exception('You are generating a module with an import "import unittest.mock". '
                            'Do not mock out modules when printing the yaml')
        non_payload_outputs = [out.name for out in self.get_outputs() if 'Payload' not in out.selector]
        if len(non_payload_outputs):
            raise Exception('These outputs do not specify "$.Payload." in selector, but they should: Step '
                            + self.name + ':' + str(non_payload_outputs))

    def get_required_file_imports(self):
        python_file = inspect.getmodule(self).__file__
        with open(python_file, "r") as f:
            python_lines = f.readlines()
        import_lines = [line for line in python_lines if 'import' in line]
        modules = [import_line.strip().split(" ")[1] for import_line in import_lines]
        required_modules = [module for module in modules if self.requires_yaml_import(module)]
        return required_modules

    @staticmethod
    def requires_yaml_import(module: str):
        return '..' not in module and module.split('.')[0] not in ['adk', 'typing', 'unittest', 'pytest']
