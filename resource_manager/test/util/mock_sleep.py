"""
  A utility that can be used to replace time.time and time.sleep used by utilities
  To use in a test @patch('time.time') and @patch('time.sleep')
  then replace the methods with MockSleep methods for the duration of the test.

  Example:
    @patch('time.sleep')
    @patch('time.time')
    def test_method(self, patched_time, patched_sleep):
        mock_sleep = MockSleep()
        patched_time.side_effect = mock_sleep.time
        patched_sleep.side_effect = mock_sleep.sleep

  During the test call to time.time will be directed to mock_sleep.time
   calls to time.sleep will be directed to mock_sleep.sleep which will update the mock time and return
"""


class MockSleep:
    def __init__(self):
        self._time_now = 0

    def time(self):
        return self._time_now

    def sleep(self, sleep_sec):
        self._time_now += sleep_sec
