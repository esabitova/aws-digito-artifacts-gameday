import unittest
import pytest

from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError
from botocore.paginate import PageIterator

import resource_manager.src.util.boto3_client_factory as client_factory
import resource_manager.src.util.ecs_utils as ecs_utils
import documents.util.scripts.test.test_ecs_util as test_ecs_util
from resource_manager.test.util.mock_sleep import MockSleep


def get_list_container_instances_side_effect_with_pages(pages, number_of_nodes):
    result = []
    instance_id = 0
    for i in range(0, pages):
        page_result = {"containerInstanceArns": []}
        for j in range(0, number_of_nodes):
            instance_id += 1
            instance_name = f"test{instance_id}"
            page_result['containerInstanceArns'].append(instance_name)
        result.append(page_result)
    return result


def get_paginate_side_effect(number_of_pages, number_of_nodes):
    class PageIteratorMock(PageIterator):
        def __init__(self):
            super(PageIteratorMock, self).__init__(
                self,
                input_token='input_token',
                output_token='output_token',
                more_results='more_results',
                result_keys='result_keys',
                non_aggregate_keys='non_aggregate_keys',
                limit_key='limit_key',
                max_items='max_items',
                starting_token='starting_token',
                page_size='page_size',
                op_kwargs='op_kwargs'
            )

        def __iter__(self):
            snapshots = get_list_container_instances_side_effect_with_pages(number_of_pages, number_of_nodes)
            for snapshot in snapshots:
                yield snapshot

    class PaginateMock(MagicMock):
        def paginate(self, cluster, status):
            paginator = PageIteratorMock()
            return paginator

    return PaginateMock


@pytest.mark.unit_test
class TestEcsUtil(unittest.TestCase):

    def setUp(self):
        self.session_mock = MagicMock()
        self.mock_ecs = MagicMock()
        self.client_side_effect_map = {
            'ecs': self.mock_ecs
        }
        self.session_mock.client.side_effect = lambda service_name, config=None: \
            self.client_side_effect_map.get(service_name)

    def tearDown(self):
        # Clean client factory cache after each test.
        client_factory.clients = {}
        client_factory.resources = {}

    def test_create_new_task_def(self):
        self.mock_ecs.describe_task_definition.return_value = test_ecs_util.get_task_definition()
        self.mock_ecs.register_task_definition.return_value = {"taskDefinition":
                                                               {"taskDefinitionArn": test_ecs_util.TD_ARN_NEW}
                                                               }
        res = ecs_utils.create_new_task_def(test_ecs_util.TD_ARN, self.session_mock)
        self.mock_ecs.describe_task_definition.assert_called_once_with(
            taskDefinition=test_ecs_util.TD_ARN
        )
        self.mock_ecs.describe_task_definition.assert_called_once()
        self.assertEqual(test_ecs_util.TD_ARN_NEW, res)

    def test_create_new_task_def_wrong_td_provided(self):
        self.mock_ecs.describe_task_definition.side_effect = ClientError(
            error_response={"Error": {"Code": "ClientException"}},
            operation_name='DescribeTaskDefinition'
        )
        with pytest.raises(ClientError) as client_error:
            ecs_utils.create_new_task_def(test_ecs_util.TD_ARN, self.session_mock)
        self.mock_ecs.describe_task_definition.assert_called_once_with(taskDefinition=test_ecs_util.TD_ARN)
        self.assertEqual("ClientException", client_error.value.response['Error']['Code'])

    def test_check_td_exits_true(self):
        self.mock_ecs.describe_task_definition.return_value = test_ecs_util.get_task_definition()
        res = ecs_utils.check_td_exits(test_ecs_util.TD_ARN, self.session_mock)
        self.mock_ecs.describe_task_definition.assert_called_once_with(taskDefinition=test_ecs_util.TD_ARN)
        self.assertTrue(res)

    def test_check_td_exits_doesnt_exist(self):
        self.mock_ecs.describe_task_definition.side_effect = ClientError(
            error_response={"Error":
                            {
                                "Code": "ClientException",
                                "Message": "The specified task definition does not exist"
                            }
                            },
            operation_name='DescribeTaskDefinition'
        )
        res = ecs_utils.check_td_exits(test_ecs_util.TD_ARN, self.session_mock)
        self.mock_ecs.describe_task_definition.assert_called_once_with(taskDefinition=test_ecs_util.TD_ARN)
        self.assertFalse(res)

    def test_check_td_exits_inactive(self):
        self.mock_ecs.describe_task_definition.return_value = test_ecs_util.get_task_definition()
        self.mock_ecs.describe_task_definition.return_value['taskDefinition']['status'] = 'INACTIVE'
        res = ecs_utils.check_td_exits(test_ecs_util.TD_ARN, self.session_mock)
        self.mock_ecs.describe_task_definition.assert_called_once_with(taskDefinition=test_ecs_util.TD_ARN)
        self.assertFalse(res)

    @patch('time.sleep')
    @patch('time.time')
    def test_delete_task_definition(self, patched_time, patched_sleep):
        self.mock_ecs.update_service.return_value = {}
        mock_sleep = MockSleep()
        patched_sleep.side_effect = mock_sleep.sleep
        patched_time.side_effect = mock_sleep.time
        self.mock_ecs.describe_task_definition.side_effect = [
            test_ecs_util.get_task_definition(),
            ClientError(
                error_response={
                    "Error":
                        {
                            "Code": "ClientException",
                            "Message": "The specified task definition does not exist"
                        }
                },
                operation_name='DescribeTaskDefinition'
            )
        ]
        ecs_utils.delete_task_definition(
            td_arn=test_ecs_util.TD_ARN,
            service_name=test_ecs_util.SERVICE_NAME,
            cluster_name=test_ecs_util.CLUSTER_NAME,
            old_td_arn=test_ecs_util.TD_ARN_2,
            wait_sec=900,
            delay_sec=15,
            session=self.session_mock)
        self.mock_ecs.describe_task_definition.assert_called_with(
            taskDefinition=test_ecs_util.TD_ARN
        )
        self.mock_ecs.deregister_task_definition.assert_called_once_with(
            taskDefinition=test_ecs_util.TD_ARN
        )
        self.mock_ecs.update_service.assert_called_once_with(
            service=test_ecs_util.SERVICE_NAME,
            cluster=test_ecs_util.CLUSTER_NAME,
            taskDefinition=test_ecs_util.TD_ARN_2
        )

    @patch('time.sleep')
    @patch('time.time')
    def test_delete_td_and_wait(self, patched_time, patched_sleep):
        mock_sleep = MockSleep()
        patched_sleep.side_effect = mock_sleep.sleep
        patched_time.side_effect = mock_sleep.time
        self.mock_ecs.describe_task_definition.side_effect = [
            test_ecs_util.get_task_definition(),
            ClientError(
                error_response={
                    "Error":
                        {
                            "Code": "ClientException",
                            "Message": "The specified task definition does not exist"
                        }
                },
                operation_name='DescribeTaskDefinition'
            )
        ]
        ecs_utils.delete_td_and_wait(test_ecs_util.TD_ARN, 900, 15, self.session_mock)
        self.mock_ecs.describe_task_definition.assert_called_with(
            taskDefinition=test_ecs_util.TD_ARN
        )
        self.mock_ecs.deregister_task_definition.assert_called_once_with(
            taskDefinition=test_ecs_util.TD_ARN
        )

    @patch('time.sleep')
    @patch('time.time')
    def test_delete_td_and_wait_timeout(self, patched_time, patched_sleep):
        mock_sleep = MockSleep()
        patched_sleep.side_effect = mock_sleep.sleep
        patched_time.side_effect = mock_sleep.time
        self.mock_ecs.describe_task_definition.return_value = test_ecs_util.get_task_definition()
        self.mock_ecs.deregister_task_definition.return_value = {}

        with pytest.raises(TimeoutError) as timeout_error:
            ecs_utils.delete_td_and_wait(test_ecs_util.TD_ARN, 900, 15, self.session_mock)

        assert 'Timeout of waiting the task definition deleted' in str(timeout_error.value)

    def test_get_amount_of_tasks(self):
        self.mock_ecs.list_tasks.return_value = {"taskArns": [
            test_ecs_util.TD_ARN_2,
            test_ecs_util.TD_ARN_2]
        }
        res = ecs_utils.get_amount_of_tasks(test_ecs_util.CLUSTER_NAME,
                                            test_ecs_util.SERVICE_NAME,
                                            self.session_mock)

        self.assertEqual(2, res)
        self.mock_ecs.list_tasks.assert_called_with(
            cluster=test_ecs_util.CLUSTER_NAME,
            serviceName=test_ecs_util.SERVICE_NAME
        )
        self.mock_ecs.list_tasks.assert_called_once_with(
            cluster=test_ecs_util.CLUSTER_NAME,
            serviceName=test_ecs_util.SERVICE_NAME
        )

    def test_get_container_definitions(self):
        self.mock_ecs.describe_task_definition.return_value = test_ecs_util.get_task_definition()

        res = ecs_utils.get_container_definitions(test_ecs_util.TD_ARN,
                                                  self.session_mock)
        cpu = res["cpu"]
        memory = res["memory"]

        self.assertEqual(256, cpu)
        self.assertEqual(512, memory)
        self.mock_ecs.describe_task_definition.assert_called_with(
            taskDefinition=test_ecs_util.TD_ARN
        )
        self.mock_ecs.describe_task_definition.assert_called_once_with(
            taskDefinition=test_ecs_util.TD_ARN
        )

    @patch('time.sleep')
    @patch('time.time')
    def test_wait_stable_service(self, patched_time, patched_sleep):
        mock_sleep = MockSleep()
        patched_sleep.side_effect = mock_sleep.sleep
        patched_time.side_effect = mock_sleep.time
        res = ecs_utils.wait_services_stable(test_ecs_util.CLUSTER_NAME,
                                             test_ecs_util.SERVICE_NAME,
                                             self.session_mock)
        self.assertEqual(None, res)

    def test_get_number_of_nodes_in_status(self):
        self.mock_ecs.describe_clusters.return_value = test_ecs_util.get_cluster()
        self.mock_ecs.get_paginator.side_effect = get_paginate_side_effect(3, 10)

        result = ecs_utils.get_number_of_nodes_in_status(self.session_mock,
                                                         test_ecs_util.CLUSTER_NAME,
                                                         'ACTIVE')
        self.mock_ecs.describe_clusters.assert_called_once_with(
            clusters=[test_ecs_util.CLUSTER_NAME]
        )
        self.assertEqual(30, result)

    def test_get_number_of_nodes_in_status_no_cluster(self):
        self.mock_ecs.describe_clusters.return_value = test_ecs_util.get_cluster(True)
        self.mock_ecs.list_container_instances.return_value = {
            "containerInstanceArns": [
                "test1",
                "test2"
            ]
        }
        with pytest.raises(ClientError) as client_error:
            ecs_utils.get_number_of_nodes_in_status(self.session_mock,
                                                    test_ecs_util.CLUSTER_NAME,
                                                    'ACTIVE')
        self.mock_ecs.describe_clusters.assert_called_once_with(
            clusters=[test_ecs_util.CLUSTER_NAME]
        )
        self.mock_ecs.list_container_instances.assert_not_called()
        self.assertEqual(f"An error occurred (ClusterNotFound) when calling the ListContainerInstances operation: "
                         f"Could not find cluster: {test_ecs_util.CLUSTER_NAME}",
                         str(client_error.value))
