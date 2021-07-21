import time
from abc import ABC
from typing import List, Dict

from adk.src.adk.domain.non_retriable_exception import NonRetriableException
from adk.src.adk.parent_steps.automation.assert_resource_step import AssertResourceStep


class WaitForResourceStep(AssertResourceStep, ABC):
    """
    aws:waitForAwsResourceProperty implementation
    Will wait for the aws service call to respond as indicated below.
    This class behaves very similar to AwsApiStep (in fact, it is a subclass).
    This class may be subclassed in order to create a Wait for Resource step.
    Alternatively, use the SimpleWaitForResource to use this without creating a new subclass.
    """

    def __init__(self, name: str, service: str, camel_case_api: str, selector: str, desired_values: List,
                 api_params: Dict, description: str = '', python_api: str = None):
        super().__init__(name=name, service=service, camel_case_api=camel_case_api, selector=selector,
                         desired_values=desired_values, api_params=api_params, description=description,
                         python_api=python_api)

    def get_action(self) -> str:
        return 'aws:waitForAwsResourceProperty'

    def execute_step(self, params: dict) -> dict:
        timeout = self._timeout_seconds + time.time()
        last_exception = None
        while time.time() < timeout:
            try:
                return super().execute_step(params)
            except NonRetriableException as exc:
                raise exc
            except Exception as exc:
                print("Received exception when hitting AWS api " + self._service + "." + self.get_camel_case_api()
                      + ". Will try again in 3 seconds: " + str(exc))
                last_exception = exc
            time.sleep(3)
        error_msg = 'Response received for API ' + self.get_service() + ':' + self.get_python_api() +\
                    ' did not match selector values'
        if last_exception is not None:
            raise Exception(error_msg) from last_exception
        raise Exception(error_msg)
