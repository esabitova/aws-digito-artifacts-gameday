import unittest
from unittest.mock import patch, MagicMock, call

import pytest

import documents.util.scripts.test.test_elasticache_util as test_elasticache_util
import resource_manager.src.util.elasticache_utils as elasticache_utils
from resource_manager.test.util.mock_sleep import MockSleep


@pytest.mark.unit_test
class TestElasticacheUtil(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('boto3.client')
        self.client = self.patcher.start()
        self.session_mock = MagicMock()
        self.mock_elasticache = MagicMock()
        self.side_effect_map = {
            'elasticache': self.mock_elasticache
        }
        self.client.side_effect = lambda service_name, config=None: self.side_effect_map.get(service_name)
        self.session_mock.client.side_effect = lambda service_name, config=None: \
            self.side_effect_map.get(service_name)

    def tearDown(self):
        self.patcher.stop()

    def test_count_replicas_in_replication_group(self):
        self.mock_elasticache.describe_replication_groups.return_value = \
            test_elasticache_util.get_describe_replication_groups(
                test_elasticache_util.REPLICATION_GROUP_ID, 3, 3
            )
        res = elasticache_utils.count_replicas_in_replication_group(
            self.session_mock,
            test_elasticache_util.REPLICATION_GROUP_ID
        )
        self.mock_elasticache.describe_replication_groups.assert_called_once_with(
            ReplicationGroupId=test_elasticache_util.REPLICATION_GROUP_ID
        )
        self.assertEqual(2, res)

    @patch('time.sleep')
    @patch('time.time')
    def test_wait_for_available_status_on_rg_and_replicas(self, patched_time, patched_sleep):
        mock_sleep = MockSleep()
        patched_time.side_effect = mock_sleep.time
        patched_sleep.side_effect = mock_sleep.sleep

        self.mock_elasticache.describe_replication_groups.side_effect = [
            test_elasticache_util.get_describe_replication_groups(
                test_elasticache_util.REPLICATION_GROUP_ID, 2, 3
            ),
            test_elasticache_util.get_describe_replication_groups(
                test_elasticache_util.REPLICATION_GROUP_ID, 2, 3
            ),
            test_elasticache_util.get_describe_replication_groups(
                test_elasticache_util.REPLICATION_GROUP_ID, 3, 3
            )
        ]

        res = elasticache_utils.wait_for_available_status_on_rg_and_replicas(
            self.session_mock,
            test_elasticache_util.REPLICATION_GROUP_ID
        )

        self.assertEqual(True, res)
        self.mock_elasticache.describe_replication_groups.assert_called_with(
            ReplicationGroupId=test_elasticache_util.REPLICATION_GROUP_ID
        )

    @patch('time.sleep')
    @patch('time.time')
    def test_wait_for_available_status_on_rg_and_replicas_timeout(self, patched_time, patched_sleep):
        mock_sleep = MockSleep()
        patched_time.side_effect = mock_sleep.time
        patched_sleep.side_effect = mock_sleep.sleep
        time_to_wait = 900
        self.mock_elasticache.describe_replication_groups.return_value = \
            test_elasticache_util.get_describe_replication_groups(
                test_elasticache_util.REPLICATION_GROUP_ID, 2, 30
            )

        with pytest.raises(TimeoutError) as timeout_error:
            res = elasticache_utils.wait_for_available_status_on_rg_and_replicas(
                self.session_mock,
                test_elasticache_util.REPLICATION_GROUP_ID
            )
            print(res)
        self.mock_elasticache.describe_replication_groups.assert_called_with(
            ReplicationGroupId=test_elasticache_util.REPLICATION_GROUP_ID
        )
        self.assertEqual(f'Replication group {test_elasticache_util.REPLICATION_GROUP_ID} couldn\'t '
                         f'be scaled in {time_to_wait} seconds', str(timeout_error.value))

    @patch('time.sleep')
    @patch('time.time')
    def test_increase_replicas_in_replication_group(self, patched_time, patched_sleep):
        mock_sleep = MockSleep()
        patched_time.side_effect = mock_sleep.time
        patched_sleep.side_effect = mock_sleep.sleep

        desired_count = 2

        self.mock_elasticache.describe_replication_groups.side_effect = [
            test_elasticache_util.get_describe_replication_groups(
                test_elasticache_util.REPLICATION_GROUP_ID, desired_count + 1, desired_count
            ),
            test_elasticache_util.get_describe_replication_groups(
                test_elasticache_util.REPLICATION_GROUP_ID, desired_count + 1, desired_count
            ),
            test_elasticache_util.get_describe_replication_groups(
                test_elasticache_util.REPLICATION_GROUP_ID, desired_count + 1, desired_count + 1
            )
        ]
        describe_calls = [
            call(ReplicationGroupId=test_elasticache_util.REPLICATION_GROUP_ID),
            call(ReplicationGroupId=test_elasticache_util.REPLICATION_GROUP_ID)
        ]
        elasticache_utils.increase_replicas_in_replication_group(
            self.session_mock,
            test_elasticache_util.REPLICATION_GROUP_ID,
            desired_count
        )
        self.mock_elasticache.increase_replica_count.assert_called_once_with(
            ReplicationGroupId=test_elasticache_util.REPLICATION_GROUP_ID,
            NewReplicaCount=desired_count,
            ApplyImmediately=True
        )
        self.mock_elasticache.describe_replication_groups.assert_has_calls(
            describe_calls
        )

    @patch('time.sleep')
    @patch('time.time')
    def test_decrease_replicas_in_replication_group(self, patched_time, patched_sleep):
        mock_sleep = MockSleep()
        patched_time.side_effect = mock_sleep.time
        patched_sleep.side_effect = mock_sleep.sleep

        desired_count = 2

        self.mock_elasticache.describe_replication_groups.side_effect = [
            test_elasticache_util.get_describe_replication_groups(
                test_elasticache_util.REPLICATION_GROUP_ID, desired_count + 1, desired_count + 3
            ),
            test_elasticache_util.get_describe_replication_groups(
                test_elasticache_util.REPLICATION_GROUP_ID, desired_count + 1, desired_count + 3
            ),
            test_elasticache_util.get_describe_replication_groups(
                test_elasticache_util.REPLICATION_GROUP_ID, desired_count + 1, desired_count + 1
            )
        ]
        describe_calls = [
            call(ReplicationGroupId=test_elasticache_util.REPLICATION_GROUP_ID),
            call(ReplicationGroupId=test_elasticache_util.REPLICATION_GROUP_ID)
        ]
        elasticache_utils.decrease_replicas_in_replication_group(
            self.session_mock,
            test_elasticache_util.REPLICATION_GROUP_ID,
            desired_count
        )
        self.mock_elasticache.decrease_replica_count.assert_called_once_with(
            ReplicationGroupId=test_elasticache_util.REPLICATION_GROUP_ID,
            NewReplicaCount=desired_count,
            ApplyImmediately=True
        )
        self.mock_elasticache.describe_replication_groups.assert_has_calls(
            describe_calls
        )

    @patch('time.sleep')
    @patch('time.time')
    def test_wait_for_replication_group_available(self, patched_time, patched_sleep):
        mock_sleep = MockSleep()
        patched_sleep.side_effect = mock_sleep.sleep
        patched_time.side_effect = mock_sleep.time
        response = elasticache_utils.wait_for_replication_group_available(
            self.session_mock,
            test_elasticache_util.REPLICATION_GROUP_ID
        )
        self.assertEqual(None, response)

    def test_get_cache_parameter_group(self):
        self.mock_elasticache.describe_replication_groups.return_value = \
            test_elasticache_util.get_describe_replication_groups(test_elasticache_util.REPLICATION_GROUP_ID, 4, 4)
        self.mock_elasticache.describe_cache_clusters.return_value = \
            test_elasticache_util.get_describe_cache_clusters()
        res = elasticache_utils.get_cache_parameter_group(
            self.session_mock,
            test_elasticache_util.REPLICATION_GROUP_ID)
        self.mock_elasticache.describe_replication_groups.assert_called_once_with(
            ReplicationGroupId=test_elasticache_util.REPLICATION_GROUP_ID
        )
        self.mock_elasticache.describe_cache_clusters.assert_called_once_with(
            CacheClusterId=f"{test_elasticache_util.REPLICATION_GROUP_ID}-001"
        )
        self.assertEqual('default.redis6.x.cluster.on', res)

    @patch('time.sleep')
    @patch('time.time')
    def test_wait_for_parameters_in_sync(self, patched_time, patched_sleep):
        mock_sleep = MockSleep()
        patched_sleep.side_effect = mock_sleep.sleep
        patched_time.side_effect = mock_sleep.time
        self.mock_elasticache.describe_replication_groups.return_value = \
            test_elasticache_util.get_describe_replication_groups(test_elasticache_util.REPLICATION_GROUP_ID, 4, 4)
        self.mock_elasticache.describe_cache_clusters.side_effect = [
            test_elasticache_util.get_describe_cache_clusters(
                cluster_id='001',
                cache_parameter_group_status="applying"
            ),
            test_elasticache_util.get_describe_cache_clusters(
                cluster_id='002',
                cache_parameter_group_status="applying"
            ),
            test_elasticache_util.get_describe_cache_clusters(
                cluster_id='003',
                cache_parameter_group_status="applying"
            ),
            test_elasticache_util.get_describe_cache_clusters(
                cluster_id='004',
                cache_parameter_group_status="applying"
            ),
            test_elasticache_util.get_describe_cache_clusters(
                cluster_id='001',
                cache_parameter_group_status="applying"
            ),
            test_elasticache_util.get_describe_cache_clusters(
                cluster_id='002',
                cache_parameter_group_status="in-sync"
            ),
            test_elasticache_util.get_describe_cache_clusters(
                cluster_id='003',
                cache_parameter_group_status="in-sync"
            ),
            test_elasticache_util.get_describe_cache_clusters(
                cluster_id='004',
                cache_parameter_group_status="in-sync"
            ),
            test_elasticache_util.get_describe_cache_clusters(
                cluster_id='001',
                cache_parameter_group_status="in-sync"
            ),
        ]
        calls = [
            call(CacheClusterId=test_elasticache_util.REPLICATION_GROUP_ID + '-' + cluster_id)
            for cluster_id in ['001', '002', '003', '004', '001', '002', '004', '001', '003']
        ]
        elasticache_utils.wait_for_parameters_in_sync(
            self.session_mock,
            test_elasticache_util.REPLICATION_GROUP_ID
        )
        self.mock_elasticache.describe_replication_groups.assert_called_once_with(
            ReplicationGroupId=test_elasticache_util.REPLICATION_GROUP_ID
        )
        self.mock_elasticache.describe_cache_clusters.assert_has_calls(calls)

    @patch('time.sleep')
    @patch('time.time')
    def test_wait_for_parameters_in_sync_timeout(self, patched_time, patched_sleep):
        mock_sleep = MockSleep()
        patched_sleep.side_effect = mock_sleep.sleep
        patched_time.side_effect = mock_sleep.time
        self.mock_elasticache.describe_replication_groups.return_value = \
            test_elasticache_util.get_describe_replication_groups(test_elasticache_util.REPLICATION_GROUP_ID, 4, 4)
        self.mock_elasticache.describe_cache_clusters.return_value = test_elasticache_util.get_describe_cache_clusters(
            cluster_id='001',
            cache_parameter_group_status="applying"
        )
        with pytest.raises(TimeoutError) as timeout_error:
            elasticache_utils.wait_for_parameters_in_sync(
                self.session_mock,
                test_elasticache_util.REPLICATION_GROUP_ID
            )
        self.assertEqual(f"All CacheParameterGroups for replicas in rg {test_elasticache_util.REPLICATION_GROUP_ID} "
                         f"didn't become available in 900 seconds",
                         str(timeout_error.value)
                         )

    @patch('time.sleep')
    @patch('time.time')
    def test_delete_cache_parameter_group(self, patched_time, patched_sleep):
        mock_sleep = MockSleep()
        patched_sleep.side_effect = mock_sleep.sleep
        patched_time.side_effect = mock_sleep.time

        old_cache_param_group_name = 'cpg_old'
        new_cache_param_group_name = 'cpg_new'
        self.mock_elasticache.describe_replication_groups.return_value = \
            test_elasticache_util.get_describe_replication_groups(test_elasticache_util.REPLICATION_GROUP_ID, 1, 1)
        self.mock_elasticache.describe_cache_clusters.side_effect = [
            test_elasticache_util.get_describe_cache_clusters(
                cluster_id='001',
                cache_parameter_group_status="in-sync"
            ),
        ]
        self.mock_elasticache.modify_replication_group.return_value = {}
        self.mock_elasticache.delete_cache_parameter_group.return_value = {}
        elasticache_utils.delete_cache_parameter_group(
            self.session_mock,
            new_cache_param_group_name,
            test_elasticache_util.REPLICATION_GROUP_ID,
            old_cache_param_group_name
        )
        self.mock_elasticache.describe_replication_groups.assert_called_once_with(
            ReplicationGroupId=test_elasticache_util.REPLICATION_GROUP_ID
        )
        self.mock_elasticache.describe_cache_clusters.assert_called_once_with(
            CacheClusterId=test_elasticache_util.REPLICATION_GROUP_ID + '-001'
        )
        self.mock_elasticache.modify_replication_group.assert_called_once_with(
            CacheParameterGroupName=old_cache_param_group_name,
            ReplicationGroupId=test_elasticache_util.REPLICATION_GROUP_ID,
            ApplyImmediately=True
        )
        self.mock_elasticache.delete_cache_parameter_group.assert_called_once_with(
            CacheParameterGroupName=new_cache_param_group_name
        )
