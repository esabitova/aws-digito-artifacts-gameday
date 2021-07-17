import unittest
import pytest
import documents.util.scripts.src.elasticache_util as elasticache_util
import documents.util.scripts.test.test_data_provider as test_data_provider
from unittest.mock import patch, MagicMock

from documents.util.scripts.test.mock_sleep import MockSleep

ELASTICACHE_REPLICATION_GROUP_ID = "rd-id-1234567890"


def get_describe_replication_groups(rg_id, memberclusters_count, node_count):
    member_clusters = [f"{rg_id}-00{x}" for x in range(1, memberclusters_count + 1)]
    replicas = [
        {
            "CacheClusterId": f"{rg_id}-00{x}",
            "CacheNodeId": "0001",
            "ReadEndpoint": {
                "Address": f"{rg_id}-00{x}.00yu6x.0001.euc1.cache.amazonaws.com",
                "Port": 6379
            },
            "PreferredAvailabilityZone": "eu-central-1a",
            "CurrentRole": "replica"
        } for x in range(2, node_count + 1)]
    nodegroup_members = [{
        "CacheClusterId": f"{rg_id}-001",
        "CacheNodeId": "0001",
        "ReadEndpoint": {
            "Address": f"{rg_id}-001.00yu6x.0001.euc1.cache.amazonaws.com",
            "Port": 6379
        },
        "PreferredAvailabilityZone": "eu-central-1a",
        "CurrentRole": "primary"
    }] + replicas

    result = {
        "ReplicationGroups": [
            {
                "ReplicationGroupId": rg_id,
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
                            "Address": f"{rg_id}.00yu6x.ng.0001.euc1.cache.amazonaws.com",
                            "Port": 6379
                        },
                        "ReaderEndpoint": {
                            "Address": f"{rg_id}-ro.00yu6x.ng.0001.euc1.cache.amazonaws.com",
                            "Port": 6379
                        },
                        "NodeGroupMembers": nodegroup_members
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
                "ARN": f"arn:aws:elasticache:eu-central-1:{test_data_provider.ACCOUNT_ID}:replicationgroup:{rg_id}"
            }
        ]
    }
    return result


@pytest.mark.unit_test
class TestBackupUtil(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('boto3.client')
        self.client = self.patcher.start()
        self.mock_elasticache = MagicMock()
        self.side_effect_map = {
            'elasticache': self.mock_elasticache,
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
            elasticache_util.check_required_params(required_params, events)
        assert 'Requires test2 in events' in str(key_error.value)

    def test_verify_all_nodes_in_rg_available(self):
        events = {
            "ReplicationGroupId": ELASTICACHE_REPLICATION_GROUP_ID
        }
        self.mock_elasticache.describe_replication_groups.return_value = \
            get_describe_replication_groups(ELASTICACHE_REPLICATION_GROUP_ID, 3, 3)
        elasticache_util.verify_all_nodes_in_rg_available(events, None)
        self.mock_elasticache.describe_replication_groups.assert_called_with(
            ReplicationGroupId=ELASTICACHE_REPLICATION_GROUP_ID
        )

    @patch('time.sleep')
    @patch('time.time')
    def test_verify_all_nodes_in_rg_available_timeout(self, patched_time, patched_sleep):
        mock_sleep = MockSleep()
        patched_time.side_effect = mock_sleep.time
        patched_sleep.side_effect = mock_sleep.sleep
        events = {
            "ReplicationGroupId": ELASTICACHE_REPLICATION_GROUP_ID
        }
        time_to_wait = 900
        self.mock_elasticache.describe_replication_groups.return_value = \
            get_describe_replication_groups(ELASTICACHE_REPLICATION_GROUP_ID, 2, 3)
        with pytest.raises(TimeoutError) as timeout_error:
            elasticache_util.verify_all_nodes_in_rg_available(events, None)
        self.mock_elasticache.describe_replication_groups.assert_called_with(
            ReplicationGroupId=ELASTICACHE_REPLICATION_GROUP_ID
        )
        self.assertEqual(f'Replication group {ELASTICACHE_REPLICATION_GROUP_ID} couldn\'t '
                         f'be scaled in {time_to_wait} seconds', str(timeout_error.value))
