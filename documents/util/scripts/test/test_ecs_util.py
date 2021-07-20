import unittest
import pytest
import documents.util.scripts.src.ecs_util as ecs_util
import documents.util.scripts.test.test_data_provider as test_data_provider
from botocore.exceptions import ClientError
from unittest.mock import patch, MagicMock

TD_FAMILY = "hello_world"
TD_ARN = f"arn:aws:ecs:eu-central-1:{test_data_provider.ACCOUNT_ID}:task-definition/{TD_FAMILY}:1"
TD_ARN_2 = f"arn:aws:ecs:eu-central-1:{test_data_provider.ACCOUNT_ID}:task-definition/{TD_FAMILY}:2"
TD_ARN_NEW = f"arn:aws:ecs:eu-central-1:{test_data_provider.ACCOUNT_ID}:task-definition/new-{TD_FAMILY}:1"
SERVICE_NAME = "Test-service-name"
CLUSTER_NAME = "Test-cluster-name"


def get_task_definition():
    res = {
        "taskDefinition": {
            "taskDefinitionArn": TD_ARN,
            "containerDefinitions": [
                {
                    "name": "hello_world",
                    "image": "amazon/amazon-ecs-sample",
                    "cpu": 256,
                    "memory": 512,
                    "links": [],
                    "portMappings": [],
                    "essential": True,
                    "entryPoint": [
                        "/usr/sbin/apache2",
                        "-D",
                        "FOREGROUND"
                    ],
                    "command": [],
                    "environment": [],
                    "environmentFiles": [],
                    "mountPoints": [],
                    "volumesFrom": [],
                    "secrets": [],
                    "dnsServers": [],
                    "dnsSearchDomains": [],
                    "extraHosts": [],
                    "dockerSecurityOptions": [],
                    "dockerLabels": {},
                    "ulimits": [],
                    "systemControls": []
                }
            ],
            "family": TD_FAMILY,
            "revision": 1,
            "volumes": [],
            "status": "ACTIVE",
            "requiresAttributes": [
                {
                    "name": "com.amazonaws.ecs.capability.docker-remote-api.1.17"
                },
                {
                    "name": "com.amazonaws.ecs.capability.docker-remote-api.1.18"
                }
            ],
            "placementConstraints": [],
            "compatibilities": [
                "EXTERNAL",
                "EC2"
            ],
            "registeredAt": "2021-07-14T15:53:11.028000+03:00",
            "registeredBy": f"arn:aws:iam::{test_data_provider.ACCOUNT_ID}:user/some_username"
        }
    }
    return res


@pytest.mark.unit_test
class TestEcsUtil(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('boto3.client')
        self.client = self.patcher.start()
        self.mock_ecs = MagicMock()
        self.side_effect_map = {
            'ecs': self.mock_ecs,
        }
        self.client.side_effect = lambda service_name, config=None: self.side_effect_map.get(service_name)

    def tearDown(self):
        self.patcher.stop()

    def test_check_required_params(self):
        events = {
            'test': 'foo'
        }
        required_params = [
            'test',
            'test2'
        ]
        with pytest.raises(KeyError) as key_error:
            ecs_util.check_required_params(required_params, events)
        assert 'Requires test2 in events' in str(key_error.value)

    def test_create_new_task_definition_td_provided(self):
        events = {
            'NewTaskDefinitionArn': TD_ARN
        }
        self.mock_ecs.describe_task_definition.return_value = get_task_definition()
        res = ecs_util.create_new_task_definition(events, None)
        self.assertEqual({"TaskDefinitionArn": TD_ARN}, res)
        self.mock_ecs.describe_task_definition.assert_called_once_with(taskDefinition=TD_ARN)

    def test_create_new_task_definition_wrong_td_provided(self):
        events = {
            'NewTaskDefinitionArn': TD_ARN
        }
        self.mock_ecs.describe_task_definition.side_effect = ClientError(
            error_response={"Error": {"Code": "ClientException"}},
            operation_name='DescribeTaskDefinition'
        )
        with pytest.raises(ClientError) as client_error:
            ecs_util.create_new_task_definition(events, None)
        self.mock_ecs.describe_task_definition.assert_called_once_with(taskDefinition=TD_ARN)
        self.assertEqual("ClientException", client_error.value.response['Error']['Code'])

    def test_create_new_task_definition_no_td(self):
        events = {
            "ServiceName": SERVICE_NAME,
            "ClusterName": CLUSTER_NAME
        }

        self.mock_ecs.describe_services.return_value = {'services': [{'taskDefinition': TD_ARN}]}
        self.mock_ecs.describe_task_definition.return_value = get_task_definition()
        self.mock_ecs.register_task_definition.return_value = {"taskDefinition": {"taskDefinitionArn": TD_ARN_2}}
        res = ecs_util.create_new_task_definition(events, None)
        self.assertEqual({"TaskDefinitionArn": TD_ARN_2}, res)
        self.mock_ecs.describe_services.assert_called_once_with(
            services=[SERVICE_NAME],
            cluster=CLUSTER_NAME
        )
        self.mock_ecs.describe_task_definition.assert_called_once_with(
            taskDefinition=TD_ARN
        )
        self.mock_ecs.register_task_definition.assert_called_once()

    def test_create_new_task_definition_no_td_cpu_ram(self):
        events = {
            "ServiceName": SERVICE_NAME,
            "ClusterName": CLUSTER_NAME,
            "TaskDefinitionCPU": 6,
            "TaskDefinitionRAM": 512
        }

        self.mock_ecs.describe_services.return_value = {'services': [{'taskDefinition': TD_ARN}]}
        self.mock_ecs.describe_task_definition.return_value = get_task_definition()
        self.mock_ecs.register_task_definition.return_value = {"taskDefinition": {"taskDefinitionArn": TD_ARN_2}}
        res = ecs_util.create_new_task_definition(events, None)
        self.mock_ecs.describe_services.assert_called_once_with(
            services=[SERVICE_NAME],
            cluster=CLUSTER_NAME
        )
        self.mock_ecs.describe_task_definition.assert_called_once_with(
            taskDefinition=TD_ARN
        )
        self.mock_ecs.register_task_definition.assert_called_once()
        self.assertEqual({"TaskDefinitionArn": TD_ARN_2}, res)

    def test_create_new_task_definition_wrong_servicename(self):
        events = {
            "ServiceName": SERVICE_NAME,
            "ClusterName": CLUSTER_NAME
        }

        self.mock_ecs.describe_services.return_value = {'services': []}
        with pytest.raises(ClientError) as client_error:
            ecs_util.create_new_task_definition(events, None)
        self.mock_ecs.describe_services.assert_called_once_with(
            services=[SERVICE_NAME],
            cluster=CLUSTER_NAME
        )
        self.assertEqual("ServiceNotFound", client_error.value.response['Error']['Code'])
