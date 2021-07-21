import time
from typing import List

from adk.src.adk.domain.output import Output
from adk.src.adk.parent_steps.abstract_automation_step import AbstractAutomationStep


class SleepStep(AbstractAutomationStep):
    """
    aws:sleep implementation
    Used to sleep the execution for the specified amount of sleep_seconds.
    The python code ALSO sleeps. Be sure to mock out the sleep code externally.
    """

    def __init__(self, sleep_seconds: int, name: str = None):
        super().__init__(name if name else type(self).__name__)
        if sleep_seconds > 604800:
            raise Exception("Sleep time " + str(self.sleep_seconds) + " is greater than max of 604800")
        self.sleep_seconds = sleep_seconds

    def get_outputs(self) -> List[Output]:
        return []

    def get_inputs(self) -> list:
        return []

    def get_description(self) -> str:
        return ''

    def execute_step(self, params: dict) -> dict:
        start = time.time()
        time.sleep(self.sleep_seconds)
        # Let's check if this actually went to sleep. We will use 0.8 seconds as a rule of thumb.
        # Anything greater than that means we actually went to sleep.
        if time.time() - start > 0.8:
            print('== WARNING! == The execution actually performed a sleep. '
                  'If you are committing this code ensure that you mock out the call to time.sleep using:\n'
                  '  @patch("time.sleep", return_value=None)\n'
                  '  def test_something(self, patched_time_sleep):...')
        return {}

    def get_action(self) -> str:
        return 'aws:sleep'

    def get_yaml(self) -> str:
        return self.to_yaml(inputs={'Duration': "PT" + str(self.sleep_seconds) + "S"})
