import unittest
import pytest

from unittest.mock import MagicMock

import resource_manager.src.util.boto3_client_factory as client_factory
import resource_manager.src.util.fis_utils as fis_utils


@pytest.mark.unit_test
class TestFisUtil(unittest.TestCase):

    def setUp(self):
        self.session_mock = MagicMock()
        self.mock_fis = MagicMock()
        self.client_side_effect_map = {
            'fis': self.mock_fis
        }
        self.session_mock.client.side_effect = lambda service_name, config=None: \
            self.client_side_effect_map.get(service_name)

    def tearDown(self):
        # Clean client factory cache after each test.
        client_factory.clients = {}
        client_factory.resources = {}

    def test_get_number_of_templates_with_tag(self):
        self.mock_fis.list_experiment_templates.return_value = {
            "experimentTemplates": [
                {
                    "id": "1",
                    "tags": {
                        "Digito": "svc:test:test_tag"
                    }
                },
                {
                    "id": "2",
                    "tags": {
                        "Digito": "something:else"
                    }
                },
                {
                    "id": "3",
                    "tags": {}
                }
            ]
        }
        result = fis_utils.get_number_of_templates_with_tag(self.session_mock, "svc:test:test_tag")

        self.assertEqual(1, result)
