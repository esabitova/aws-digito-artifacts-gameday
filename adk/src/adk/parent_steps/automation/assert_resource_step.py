from typing import List, Dict

from adk.src.adk.parent_steps.automation.aws_api_step import AwsApiStep


class AssertResourceStep(AwsApiStep):
    """
    aws:assertAwsResourceProperty implementation
    Will assert that the aws service call matches one of the expected desired_values.
    This class behaves very similar to AwsApiStep (in fact, it is a subclass) and WaitForResourceStep (superclass)
    This class may be subclassed in order to create an Assert for Resource step.
    Alternatively, use the SimpleAssertResource to use this without creating a new subclass.
    """

    def __init__(self, name: str, service: str, camel_case_api: str, selector: str, desired_values: List,
                 api_params: Dict, description: str = '', python_api: str = None):
        super().__init__(name=name, service=service, camel_case_api=camel_case_api,
                         api_params=api_params, description=description, outputs=[], python_api=python_api)
        self._selector = selector
        self._desired_values = desired_values

    def get_selector(self) -> str:
        """
        Selector to search for value in the response json from the service api call.
        Example: '$.DBInstances..DBInstanceStatus'
        :return: the selector (JsonPath)
        """
        return self._selector

    def get_desired_values(self) -> List:
        """
        List of values to path to the value found by the selector.
        Example: ['started', 'in_progress']
        :return: the list of desired values for the value at the specified selector
        """
        return self._desired_values

    def get_action(self) -> str:
        return 'aws:assertAwsResourceProperty'

    def execute_step(self, params: dict) -> dict:
        response = super().execute_step(params)
        if self.get_value_from_json(response, self.get_selector(), "Selector") in self.get_desired_values():
            return {}
        else:
            raise Exception('Did not find value from ' + str(self.get_desired_values()) + ' in selector '
                            + self.get_selector() + ' for response: ' + str(response))

    def get_yaml(self):
        yaml_inputs = {**{'Service': self.get_service(),
                          'Api': self.get_camel_case_api(),
                          'PropertySelector': self.get_selector(),
                          'DesiredValues': self.get_desired_values()}
                       , **self.get_api_params()}
        return self.to_yaml(inputs=yaml_inputs)
