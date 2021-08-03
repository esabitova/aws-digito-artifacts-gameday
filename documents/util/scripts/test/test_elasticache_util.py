import unittest
from unittest.mock import patch, MagicMock

import pytest

import documents.util.scripts.src.elasticache_util as elasticache_util
import documents.util.scripts.test.test_data_provider as test_data_provider
from documents.util.scripts.test.mock_sleep import MockSleep

REPLICATION_GROUP_ID = 'redis-non-cluster-single-az-7174ddd0'
PRIMARY_CLUSTER_ID = REPLICATION_GROUP_ID + '001'


def get_sample_describe_replication_groups_response(**kwargs):
    return {
        'ReplicationGroups': [
            {
                'ReplicationGroupId': REPLICATION_GROUP_ID,
                'AutomaticFailover': kwargs.get('AutomaticFailover', 'disabled'),
                'MultiAZ': kwargs.get('MultiAZ', 'disabled'),
                'ClusterEnabled': kwargs.get('ClusterEnabled', False),
                'Status': kwargs.get('Status', 'available')
            }
        ],
        "ResponseMetadata": {
            "HTTPStatusCode": 200
        }
    }


def get_describe_replication_groups(replication_group_id, member_clusters_count, node_count):
    member_clusters = [f"{replication_group_id}-00{x}" for x in range(1, member_clusters_count + 1)]

    replicas = [{
        "CacheClusterId": f"{replication_group_id}-00{x}",
        "CacheNodeId": "0001",
        "ReadEndpoint": {
            "Address": f"{replication_group_id}-00{x}.00yu6x.0001.euc1.cache.amazonaws.com",
            "Port": 6379
        },
        "PreferredAvailabilityZone": "eu-central-1a",
        "CurrentRole": "replica"
    } for x in range(2, node_count + 1)]

    node_group_members = [{
        "CacheClusterId": f"{replication_group_id}-001",
        "CacheNodeId": "0001",
        "ReadEndpoint": {
            "Address": f"{replication_group_id}-001.00yu6x.0001.euc1.cache.amazonaws.com",
            "Port": 6379
        },
        "PreferredAvailabilityZone": "eu-central-1a",
        "CurrentRole": "primary"
    }] + replicas

    result = {
        "ReplicationGroups": [
            {
                "ReplicationGroupId": replication_group_id,
                "Description": "ElastiCache",
                "GlobalReplicationGroupInfo": {},
                "Status": "available",
                "PendingModifiedValues": {},
                "MemberClusters": member_clusters,
                "NodeGroups": [
                    {
                        "NodeGroupId": "0001",
                        "Status": "available",
                        "PrimaryEndpoint": {
                            "Address": f"{replication_group_id}.00yu6x.ng.0001.euc1.cache.amazonaws.com",
                            "Port": 6379
                        },
                        "ReaderEndpoint": {
                            "Address": f"{replication_group_id}-ro.00yu6x.ng.0001.euc1.cache.amazonaws.com",
                            "Port": 6379
                        },
                        "NodeGroupMembers": node_group_members
                    }
                ],
                "AutomaticFailover": "disabled",
                "MultiAZ": "disabled",
                "SnapshotRetentionLimit": 0,
                "SnapshotWindow": "23:30-00:30",
                "ClusterEnabled": False,
                "CacheNodeType": "cache.t2.small",
                "AuthTokenEnabled": False,
                "TransitEncryptionEnabled": False,
                "AtRestEncryptionEnabled": False,
                "ARN": f"arn:aws:elasticache:eu-central-1:{test_data_provider.ACCOUNT_ID}:replicationgroup:"
                       f"{replication_group_id}"
            }
        ]
    }
    return result


@pytest.mark.unit_test
class TestElasticacheUtil(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('boto3.client')
        self.client = self.patcher.start()
        self.mock_elasticache = MagicMock()
        self.side_effect_map = {
            'elasticache': self.mock_elasticache
        }
        self.client.side_effect = lambda service_name, config=None: self.side_effect_map.get(service_name)

    def tearDown(self):
        self.patcher.stop()

    def test_assert_cluster_mode_disabled(self):
        events = {'ReplicationGroupId': REPLICATION_GROUP_ID}
        self.mock_elasticache.describe_replication_groups.return_value = \
            get_sample_describe_replication_groups_response(ClusterEnabled=False)
        elasticache_util.assert_cluster_mode_disabled(events, None)
        self.mock_elasticache.describe_replication_groups.assert_called_with(
            ReplicationGroupId=REPLICATION_GROUP_ID
        )

    def test_assert_cluster_mode_disabled_invalid_status(self):
        events = {'ReplicationGroupId': REPLICATION_GROUP_ID}
        self.mock_elasticache.describe_replication_groups.return_value = \
            get_sample_describe_replication_groups_response(ClusterEnabled=True)

        with pytest.raises(AssertionError) as exception_info:
            elasticache_util.assert_cluster_mode_disabled(events, None)
        self.assertTrue(exception_info.match('.*'))

    def test_check_required_params(self):
        events = {'parameter_one': 'foo'}
        required_params = ['parameter_one',
                           'parameter_two']
        with pytest.raises(KeyError) as exception_info:
            elasticache_util.check_required_params(required_params, events)
        self.assertTrue(exception_info.match('.*'))

    def test_get_failover_settings(self):
        events = {'ReplicationGroupId': REPLICATION_GROUP_ID}
        self.mock_elasticache.describe_replication_groups.return_value = \
            get_sample_describe_replication_groups_response(AutomaticFailover='enabled',
                                                            MultiAZ='disabled')
        output = elasticache_util.get_failover_settings(events, None)
        self.mock_elasticache.describe_replication_groups.assert_called_with(
            ReplicationGroupId=REPLICATION_GROUP_ID
        )
        self.assertIsNotNone(output)
        self.assertEqual(True, output['AutomaticFailover'])
        self.assertEqual(False, output['MultiAZ'])

    def test_get_failover_settings_invalid_status(self):
        events = {'ReplicationGroupId': REPLICATION_GROUP_ID}
        self.mock_elasticache.describe_replication_groups.return_value = \
            get_sample_describe_replication_groups_response(AutomaticFailover='enabling',
                                                            MultiAZ='disabled')
        with pytest.raises(AssertionError) as exception_info:
            elasticache_util.get_failover_settings(events, None)
        self.assertTrue(exception_info.match('.*'))

    def test_verify_all_nodes_in_replication_group_available(self):
        events = {
            "ReplicationGroupId": REPLICATION_GROUP_ID
        }
        self.mock_elasticache.describe_replication_groups.return_value = \
            get_describe_replication_groups(REPLICATION_GROUP_ID, 3, 3)
        elasticache_util.verify_all_nodes_in_rg_available(events, None)
        self.mock_elasticache.describe_replication_groups.assert_called_with(
            ReplicationGroupId=REPLICATION_GROUP_ID
        )

    @patch('time.sleep')
    @patch('time.time')
    def test_verify_all_nodes_in_replication_group_available_timeout(self, patched_time, patched_sleep):
        mock_sleep = MockSleep()
        patched_time.side_effect = mock_sleep.time
        patched_sleep.side_effect = mock_sleep.sleep
        events = {
            "ReplicationGroupId": REPLICATION_GROUP_ID,
            "Sleep": 400
        }
        time_to_wait = 900
        self.mock_elasticache.describe_replication_groups.return_value = \
            get_describe_replication_groups(REPLICATION_GROUP_ID, 2, 3)
        with pytest.raises(TimeoutError) as timeout_error:
            elasticache_util.verify_all_nodes_in_rg_available(events, None)
        self.mock_elasticache.describe_replication_groups.assert_called_with(
            ReplicationGroupId=REPLICATION_GROUP_ID
        )
        self.assertEqual(f'Replication group {REPLICATION_GROUP_ID} couldn\'t '
                         f'be scaled in {time_to_wait} seconds', str(timeout_error.value))
