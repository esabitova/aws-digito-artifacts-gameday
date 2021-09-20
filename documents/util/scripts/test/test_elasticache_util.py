import unittest
import pytest
from unittest.mock import patch, MagicMock, call

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


def get_describe_cache_parameter_groups():
    res = \
        {
            "CacheParameterGroups": [
                {
                    "CacheParameterGroupName": "default.redis6.x.cluster.on",
                    "CacheParameterGroupFamily": "redis6.x",
                    "Description": "desc",
                    "IsGlobal": False,
                    "ARN": f"arn:aws:elasticache:{test_data_provider.AZ_USW2A}:"
                           f"{test_data_provider.ACCOUNT_ID}:parametergroup:default.redis6.x.cluster.on"
                }]
        }
    return res


def get_describe_cache_clusters(cluster_id='001',
                                engine_version="6.0.5",
                                cache_parameter_group_status="available",
                                cache_parameter_group_name="default.redis6.x.cluster.on"):
    res = \
        {
            "CacheClusters": [
                {
                    "CacheClusterId": REPLICATION_GROUP_ID + cluster_id,
                    "ClientDownloadLandingPage": "https://console.aws.amazon.com/elasticache/home#client-download:",
                    "CacheNodeType": "cache.t3.micro",
                    "Engine": "redis",
                    "EngineVersion": engine_version,
                    "CacheClusterStatus": "available",
                    "NumCacheNodes": 1,
                    "PreferredAvailabilityZone": test_data_provider.AZ_USW2A,
                    "CacheClusterCreateTime": "2021-08-16T12:56:04.349000+00:00",
                    "PreferredMaintenanceWindow": "fri:03:00-fri:04:00",
                    "PendingModifiedValues": {},
                    "CacheSecurityGroups": [],
                    "CacheParameterGroup": {
                        "CacheParameterGroupName": cache_parameter_group_name,
                        "ParameterApplyStatus": cache_parameter_group_status,
                        "CacheNodeIdsToReboot": []
                    },
                    "CacheSubnetGroupName": "elast-elast-1lqw7xzmtdyvx",
                    "AutoMinorVersionUpgrade": True,
                    "SecurityGroups": [
                        {
                            "SecurityGroupId": test_data_provider.SECURITY_GROUP,
                            "Status": "active"
                        }
                    ],
                    "ReplicationGroupId": REPLICATION_GROUP_ID,
                    "SnapshotRetentionLimit": 0,
                    "SnapshotWindow": "23:30-00:30",
                    "AuthTokenEnabled": False,
                    "TransitEncryptionEnabled": True,
                    "AtRestEncryptionEnabled": True,
                    "ARN": f"arn:aws:elasticache:{test_data_provider.AZ_USW2A}:"
                           f"{test_data_provider.ACCOUNT_ID}:cluster:{PRIMARY_CLUSTER_ID}"
                }
            ]}
    return res


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

    def test_get_custom_parameter_group(self):
        events = {
            'CustomCacheParameterGroupNamePostfix': 'TestCacheParamGroup',
            'ReplicationGroupId': REPLICATION_GROUP_ID,
            'ReservedMemoryPercent': 50,
            'ReservedMemoryValue': ""
        }
        self.mock_elasticache.describe_replication_groups.return_value = get_describe_replication_groups(
            REPLICATION_GROUP_ID, 4, 4
        )
        self.mock_elasticache.describe_cache_clusters.return_value = get_describe_cache_clusters(
            cache_parameter_group_name='test')
        self.mock_elasticache.describe_cache_parameter_groups.return_value = {
            'CacheParameterGroups': [
                {
                    'CacheParameterGroupFamily': 'FamilyName'
                }
            ]
        }
        result = elasticache_util.get_custom_parameter_group(events, {})
        self.mock_elasticache.describe_cache_parameter_groups.assert_called_once_with(
            CacheParameterGroupName='test'
        )
        self.assertEqual(
            {'CacheParameterGroupExists': 'true',
             'CacheParameterGroupFamily': 'FamilyName',
             'CustomCacheParameterGroupName': 'test'}, result)

    def test_get_custom_parameter_group_default(self):
        events = {
            'CustomCacheParameterGroupNamePostfix': 'TestCacheParamGroup',
            'ReplicationGroupId': REPLICATION_GROUP_ID,
            'ReservedMemoryPercent': 50,
            'ReservedMemoryValue': ""
        }
        self.mock_elasticache.describe_cache_parameter_groups.return_value = get_describe_cache_parameter_groups()

        self.mock_elasticache.describe_replication_groups.return_value = get_describe_replication_groups(
            REPLICATION_GROUP_ID, 4, 4
        )
        self.mock_elasticache.describe_cache_clusters.return_value = get_describe_cache_clusters()
        result = elasticache_util.get_custom_parameter_group(events, {})

        self.mock_elasticache.describe_replication_groups.assert_called_once_with(
            ReplicationGroupId=REPLICATION_GROUP_ID
        )
        self.mock_elasticache.describe_cache_clusters.assert_called_once_with(
            CacheClusterId=f"{REPLICATION_GROUP_ID}-00{1}"
        )
        self.mock_elasticache.describe_cache_parameter_groups.assert_called_once_with(
            CacheParameterGroupName='default.redis6.x.cluster.on'
        )
        self.assertEqual({'CacheParameterGroupExists': 'false',
                          'CacheParameterGroupFamily': 'redis6.x',
                          'CustomCacheParameterGroupName': 'redis6-x-TestCacheParamGroup'}, result)

    def test_get_custom_parameter_group_wrong_params_percent(self):
        events = {
            'CustomCacheParameterGroupNamePostfix': 'TestCacheParamGroup',
            'ReplicationGroupId': REPLICATION_GROUP_ID,
            'ReservedMemoryPercent': 50,
            'ReservedMemoryValue': 50
        }
        self.mock_elasticache.describe_replication_groups.return_value = get_describe_replication_groups(
            REPLICATION_GROUP_ID, 4, 4
        )
        self.mock_elasticache.describe_cache_clusters.return_value = get_describe_cache_clusters(engine_version="1")
        with pytest.raises(AssertionError) as assertion_error_percent:
            elasticache_util.get_custom_parameter_group(events, {})
        self.assertEqual('"reserved-memory-percent" parameter is supported only for Redis engine with '
                         'version higher than "3.2.4", got 1.\n'
                         'Please remove `ReservedMemoryPercent` parameter and add `ReservedMemoryValue` parameter',
                         str(assertion_error_percent.value))

    def test_get_custom_parameter_group_wrong_params_novalue(self):
        events = {
            'CustomCacheParameterGroupNamePostfix': 'TestCacheParamGroup',
            'ReplicationGroupId': REPLICATION_GROUP_ID,
            'ReservedMemoryPercent': "",
            'ReservedMemoryValue': ""
        }
        self.mock_elasticache.describe_replication_groups.return_value = get_describe_replication_groups(
            REPLICATION_GROUP_ID, 4, 4
        )
        self.mock_elasticache.describe_cache_clusters.return_value = get_describe_cache_clusters(engine_version="1")
        with pytest.raises(AssertionError) as assertion_error_novalue:
            elasticache_util.get_custom_parameter_group(events, {})
        self.assertEqual('`ReservedMemoryValue` parameter is empty and replication group engine version is 1 '
                         'which supports only `ReservedMemoryValue`',
                         str(assertion_error_novalue.value))

    @patch('time.sleep')
    @patch('time.time')
    def test_wait_for_parameters_in_sync(self, patched_time, patched_sleep):
        mock_sleep = MockSleep()
        patched_sleep.side_effect = mock_sleep.sleep
        patched_time.side_effect = mock_sleep.time
        events = {
            'ReplicationGroupId': REPLICATION_GROUP_ID,
        }
        self.mock_elasticache.describe_replication_groups.return_value = \
            get_describe_replication_groups(REPLICATION_GROUP_ID, 4, 4)
        self.mock_elasticache.describe_cache_clusters.side_effect = [
            get_describe_cache_clusters(
                cluster_id='001',
                cache_parameter_group_status="applying"
            ),
            get_describe_cache_clusters(
                cluster_id='002',
                cache_parameter_group_status="applying"
            ),
            get_describe_cache_clusters(
                cluster_id='003',
                cache_parameter_group_status="applying"
            ),
            get_describe_cache_clusters(
                cluster_id='004',
                cache_parameter_group_status="applying"
            ),
            get_describe_cache_clusters(
                cluster_id='001',
                cache_parameter_group_status="applying"
            ),
            get_describe_cache_clusters(
                cluster_id='002',
                cache_parameter_group_status="in-sync"
            ),
            get_describe_cache_clusters(
                cluster_id='003',
                cache_parameter_group_status="in-sync"
            ),
            get_describe_cache_clusters(
                cluster_id='004',
                cache_parameter_group_status="in-sync"
            ),
            get_describe_cache_clusters(
                cluster_id='001',
                cache_parameter_group_status="in-sync"
            ),
        ]
        calls = [
            call(CacheClusterId=REPLICATION_GROUP_ID + '-' + cluster_id)
            for cluster_id in ['001', '002', '003', '004', '001', '002', '004', '001', '003']
        ]
        elasticache_util.wait_for_parameters_in_sync(
            events, {}
        )
        self.mock_elasticache.describe_replication_groups.assert_called_once_with(
            ReplicationGroupId=REPLICATION_GROUP_ID
        )
        self.mock_elasticache.describe_cache_clusters.assert_has_calls(calls)

    def test_modify_cache_parameter_group_percent(self):
        events = {
            'CacheParameterGroupName': 'TestCacheParamGroup',
            'ReservedMemoryPercent': 50,
            'ReservedMemoryValue': ""
        }
        self.mock_elasticache.describe_cache_clusters.return_value = {}
        elasticache_util.modify_cache_parameter_group(events, {})

        self.mock_elasticache.modify_cache_parameter_group.assert_called_once_with(
            CacheParameterGroupName='TestCacheParamGroup',
            ParameterNameValues=[
                {
                    'ParameterName': 'reserved-memory-percent',
                    'ParameterValue': 50
                },
                {
                    'ParameterName': 'cluster-enabled',
                    'ParameterValue': 'yes'
                }
            ]
        )

    def test_modify_cache_parameter_group_value(self):
        events = {
            'CacheParameterGroupName': 'TestCacheParamGroup',
            'ReservedMemoryPercent': "",
            'ReservedMemoryValue': 50
        }
        self.mock_elasticache.describe_cache_clusters.return_value = {}
        elasticache_util.modify_cache_parameter_group(events, {})

        self.mock_elasticache.modify_cache_parameter_group.assert_called_once_with(
            CacheParameterGroupName='TestCacheParamGroup',
            ParameterNameValues=[
                {
                    'ParameterName': 'reserved-memory',
                    'ParameterValue': 50
                },
                {
                    'ParameterName': 'cluster-enabled',
                    'ParameterValue': 'yes'
                }
            ]
        )

    def test_get_cache_parameter_group(self):
        self.mock_elasticache.describe_replication_groups.return_value = \
            get_describe_replication_groups(REPLICATION_GROUP_ID, 4, 4)
        self.mock_elasticache.describe_cache_clusters.return_value = \
            get_describe_cache_clusters()
        res = elasticache_util.get_cache_parameter_group({'ReplicationGroupId': REPLICATION_GROUP_ID}, {})
        self.mock_elasticache.describe_replication_groups.assert_called_once_with(
            ReplicationGroupId=REPLICATION_GROUP_ID
        )
        self.mock_elasticache.describe_cache_clusters.assert_called_once_with(
            CacheClusterId=f"{REPLICATION_GROUP_ID}-001"
        )
        self.assertEqual('default.redis6.x.cluster.on', res)

    def test_get_cache_parameter_group_with_client(self):
        self.mock_elasticache.describe_replication_groups.return_value = \
            get_describe_replication_groups(REPLICATION_GROUP_ID, 4, 4)
        self.mock_elasticache.describe_cache_clusters.return_value = \
            get_describe_cache_clusters()
        res = elasticache_util.get_cache_parameter_group(
            {'ReplicationGroupId': REPLICATION_GROUP_ID},
            {},
            self.mock_elasticache
        )
        self.mock_elasticache.describe_replication_groups.assert_called_once_with(
            ReplicationGroupId=REPLICATION_GROUP_ID
        )
        self.mock_elasticache.describe_cache_clusters.assert_called_once_with(
            CacheClusterId=f"{REPLICATION_GROUP_ID}-001"
        )
        self.assertEqual('default.redis6.x.cluster.on', res)
