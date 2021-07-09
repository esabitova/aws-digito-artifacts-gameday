import unittest
from unittest.mock import MagicMock, patch

import pytest

from resource_manager.src.util.elb_utils import (
    send_incorrect_requests)


@pytest.mark.unit_test
class TestElbUtils(unittest.TestCase):

    def setUp(self):
        self.session_mock = MagicMock()
        self.session_mock.client.side_effect = lambda service_name, config=None: \
            self.client_side_effect_map.get(service_name)

    def tearDown(self):
        pass

    @patch('requests.sessions.Session.get',
           return_value=False)
    def test_send_incorrect_requests(self, get_mock):
        test_url: str = 'https://xyz.example'
        count: int = 10
        send_incorrect_requests(boto3_session=self.session_mock, url=test_url, count=count)
        self.assertEqual(get_mock.call_count, count)
