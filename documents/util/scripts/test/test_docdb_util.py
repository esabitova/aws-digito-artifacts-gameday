import copy
import unittest
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, call
from botocore.paginate import PageIterator

import pytest

from documents.util.scripts.src.docdb_util import count_cluster_instances, verify_db_instance_exist, \
    verify_cluster_instances, get_cluster_az, create_new_instance, get_recovery_point_input, \
    backup_cluster_instances_type, restore_to_point_in_time, restore_db_cluster_instances, rename_replaced_db_cluster, \
    rename_replaced_db_instances, rename_restored_db_instances, get_latest_snapshot_id, restore_db_cluster, \
    restore_security_group_ids, get_db_cluster_properties, wait_for_available_instances, \
    get_current_db_instance_class, scale_up_cluster, delete_list_of_instances
from documents.util.scripts.test.common_test_util import assert_having_all_not_empty_arguments_in_events
from documents.util.scripts.test.mock_sleep import MockSleep

DOCDB_AZ = "eu-central-1b"
DOCDB_CLUSTER_ID = 'docdb-cluster-id'
DOCDB_SUBNET_GROUP_NAME = 'my_subnet_group'
DOCDB_INSTANCE_ID = 'docdb-instance-id'
DOCDB_INSTANCE_STATUS = 'available'
DOCDB_ENGINE = 'docdb'
DOCDB_INSTANCE_CLASS = 'db.r5.large'
SG_ID = "sg-20a5c047"

DBSUBNET_GROUP = "default-vpc-2305ca49"
DB_CLUSER = {
    "AllocatedStorage": 1,
    "AvailabilityZones": [
        DOCDB_AZ,
        "eu-central-1c",
        "eu-central-1a"
    ],
    "BackupRetentionPeriod": 14,
    "DatabaseName": "",
    "DBClusterIdentifier": DOCDB_CLUSTER_ID,
    "DBClusterParameterGroup": DOCDB_INSTANCE_CLASS,
    "DBSubnetGroup": DBSUBNET_GROUP,
    "Status": "available",
    "EarliestRestorableTime": "2020-06-03T02:07:29.637Z",
    "Endpoint": "cluster-2.cluster-############.eu-central-1.docdb.amazonaws.com",
    "ReaderEndpoint": "cluster-2.cluster-ro-############.eu-central-1.docdb.amazonaws.com",
    "MultiAZ": "false",
    "Engine": DOCDB_ENGINE,
    "EngineVersion": "5.6.10a",
    "LatestRestorableTime": "2020-06-04T15:11:25.748Z",
    "Port": 21017,
    "MasterUsername": "admin",
    "PreferredBackupWindow": "01:55-02:25",
    "PreferredMaintenanceWindow": "thu:21:14-thu:21:44",
    "ReadReplicaIdentifiers": [],
    "DBClusterMembers": [
        {
            "DBInstanceIdentifier": DOCDB_INSTANCE_ID,
            "IsClusterWriter": "true",
            "DBClusterParameterGroupStatus": "in-sync",
            "PromotionTier": 1
        }
    ],
    "VpcSecurityGroups": [
        {
            "VpcSecurityGroupId": SG_ID,
            "Status": "active"
        }
    ],
    "HostedZoneId": "Z1RLNU0EXAMPLE",
    "StorageEncrypted": "true",
    "KmsKeyId": "arn:aws:kms:eu-central-1:123456789012:key/d1bd7c8f-5cdb-49ca-8a62-a1b2c3d4e5f6",
    "DbClusterResourceId": "cluster-AGJ7XI77XVIS6FUXHU1EXAMPLE",
    "DBClusterArn": "arn:aws:docdb:eu-central-1:123456789012:cluster:cluster-2",
    "AssociatedRoles": [],
    "IAMDatabaseAuthenticationEnabled": "false",
    "ClusterCreateTime": "2020-04-03T14:44:02.764Z",
    "EngineMode": "provisioned",
    "DeletionProtection": "false",
    "HttpEndpointEnabled": "false",
    "CopyTagsToSnapshot": "true",
    "CrossAccountClone": "false",
    "DomainMemberships": []
}
MODIFY_DB_CLUSTER_RESPONSE = {
    "DBCluster": DB_CLUSER
}
DESCRIBE_DB_CLUSTER_RESPONSE = {
    "DBClusters": [DB_CLUSER]
}
DESCRIBE_DB_INSTANCES_RESPONSE = {
    "DBInstances": [
        {
            "DBInstanceIdentifier": DOCDB_INSTANCE_ID,
            "DBInstanceClass": "db.t3.medium",
            "Engine": DOCDB_ENGINE,
            "DBInstanceStatus": DOCDB_INSTANCE_STATUS,
            "MasterUsername": "admindb",
            "Endpoint": {
                "Address": "dbinstance02-eu-central-1-435978235123-845de9e0.cfthigcesefy"
                           ".eu-central-1.docdb.amazonaws.com",
                "Port": 27017,
                "HostedZoneId": "Z1ZKU8ZZR6T7FW"
            },
            "AllocatedStorage": 1,
            "InstanceCreateTime": "2021-05-27T11:01:56.171Z",
            "PreferredBackupWindow": "22:42-23:12",
            "BackupRetentionPeriod": 1,
            "DBSecurityGroups": [],
            "VpcSecurityGroups": [
                {
                    "VpcSecurityGroupId": SG_ID,
                    "Status": "active"
                }
            ],
            "DBParameterGroups": [
                {
                    "DBParameterGroupName": "default.docdb4.0",
                    "ParameterApplyStatus": "in-sync"
                }
            ],
            "AvailabilityZone": "eu-central-1a",
            "DBSubnetGroup": {
                "DBSubnetGroupName": "docdbclustersubnetgroup-sgadyke9fwu9",
                "DBSubnetGroupDescription": "DocumentDB cluster subnet group",
                "VpcId": "vpc-013045c82df0a77c2",
                "SubnetGroupStatus": "Complete",
                "Subnets": [
                    {
                        "SubnetIdentifier": "subnet-0d9c4e55fb8ea7012",
                        "SubnetAvailabilityZone": {
                            "Name": "eu-central-1b"
                        },
                        "SubnetOutpost": {},
                        "SubnetStatus": "Active"
                    },
                    {
                        "SubnetIdentifier": "subnet-074979f248ea62162",
                        "SubnetAvailabilityZone": {
                            "Name": "eu-central-1a"
                        },
                        "SubnetOutpost": {},
                        "SubnetStatus": "Active"
                    }
                ]
            },
            "PreferredMaintenanceWindow": "sun:21:03-sun:21:33",
            "PendingModifiedValues": {},
            "MultiAZ": "false",
            "EngineVersion": "4.0.0",
            "AutoMinorVersionUpgrade": "false",
            "ReadReplicaDBInstanceIdentifiers": [],
            "LicenseModel": "na",
            "OptionGroupMemberships": [
                {
                    "OptionGroupName": "default:docdb-4-0",
                    "Status": "in-sync"
                }
            ],
            "PubliclyAccessible": "false",
            "StorageType": "aurora",
            "DbInstancePort": 0,
            "DBClusterIdentifier": "dbcluster-eu-central-1-435978235123-845de9e0",
            "StorageEncrypted": "true",
            "KmsKeyId": "arn:aws:kms:eu-central-1:435978235123:key/4cb327f0-5695-466a-a9c2-5e3e7d2fd68f",
            "DbiResourceId": "db-J6MA4FYSBEKWOJXAJGDYPFK7K4",
            "CACertificateIdentifier": "rds-ca-2019",
            "DomainMemberships": [],
            "CopyTagsToSnapshot": "false",
            "MonitoringInterval": 0,
            "PromotionTier": 1,
            "DBInstanceArn": "arn:aws:rds:eu-central-1:435978235123:db:dbinstance02-eu-central-1-435978235123-845de9e0",
            "IAMDatabaseAuthenticationEnabled": "false",
            "PerformanceInsightsEnabled": "false",
            "DeletionProtection": "false",
            "AssociatedRoles": [],
            "TagList": [],
            "CustomerOwnedIpEnabled": "false"
        }
    ]
}

DELETE_LIST_OF_INSTANCES_RESPONSE = [
    f'{DOCDB_CLUSTER_ID}-instance-1',
    f'{DOCDB_CLUSTER_ID}-instance-2'
]


def get_docdb_clusters_side_effect(number_of_instances=1):
    result = {
        'DBClusters': [
            {
                'AvailabilityZones': [DOCDB_AZ],
                'DBClusterIdentifier': DOCDB_CLUSTER_ID,
                'DBClusterMembers': []
            }
        ]
    }
    is_first = True
    for i in range(0, number_of_instances):
        instance = {'DBInstanceIdentifier': DOCDB_INSTANCE_ID + f'-{i}', 'IsClusterWriter': is_first}
        result['DBClusters'][0]['DBClusterMembers'].append(instance)
        is_first = False
    return result


def get_docdb_instances_with_status_side_effect(number_of_instances):
    result = {
        'DBInstances': []
    }
    for i in range(0, number_of_instances):
        result['DBInstances'].append({
            'DBInstanceStatus': 'available'
        })
    return result


def get_docdb_clusters_restore_date_side_effect(date):
    return {
        'DBClusters': [
            {'LatestRestorableTime': date}
        ]
    }


def get_create_db_instance_side_effect(az):
    result = {
        'DBInstance': {
            'AvailabilityZone': az
        }
    }
    return result


def get_describe_snapshots_side_effect_with_pages(pages, number_of_snapshots):
    result = []
    snapshot_id = 0
    for i in range(0, pages):
        page_result = {'DBClusterSnapshots': []}
        for j in range(0, number_of_snapshots):
            snapshot_id += 1
            snapshot = {
                'DBClusterSnapshotIdentifier': 'Snapshot' + str(snapshot_id),
                'Engine': DOCDB_ENGINE,
                'DBClusterIdentifier': DOCDB_CLUSTER_ID,
                'SnapshotCreateTime': datetime(2000, 1, 1) + timedelta(days=snapshot_id)
            }
            page_result['DBClusterSnapshots'].append(snapshot)
        result.append(page_result)
    return result


def get_docdb_instances_with_timestamp_side_effect():
    instance_new = {
        'InstanceCreateTime': datetime(2020, 12, 1),
        'DBClusterIdentifier': DOCDB_CLUSTER_ID,
        'DBInstanceClass': DOCDB_INSTANCE_CLASS
    }
    instance_old = {
        'InstanceCreateTime': datetime(2020, 1, 1),
        'DBClusterIdentifier': DOCDB_CLUSTER_ID,
        'DBInstanceClass': 'db.t3.medium'
    }
    return [{'DBInstances': [instance_new, instance_old]}]


def get_paginated_instances_side_effect():
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
            instances = get_docdb_instances_with_timestamp_side_effect()
            for instance in instances:
                yield instance

    class PaginateMock(MagicMock):
        def paginate(self, Filters):
            paginator = PageIteratorMock()
            return paginator

    return PaginateMock


def get_paginate_side_effect(number_of_pages, number_of_snapshots):
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
            snapshots = get_describe_snapshots_side_effect_with_pages(number_of_pages, number_of_snapshots)
            for snapshot in snapshots:
                yield snapshot

    class PaginateMock(MagicMock):
        def paginate(self, DBClusterIdentifier):
            paginator = PageIteratorMock()
            return paginator

    return PaginateMock


def get_docdb_instances_side_effect(az):
    return {'DBInstances': [{'AvailabilityZone': az}]}


def get_describe_db_cluster_side_effect():
    return {'DBClusters': [{
        'AvailabilityZones': ['us-east-1a', 'us-east-1b', 'us-east-1c'],
        "DBSubnetGroup": DOCDB_SUBNET_GROUP_NAME
    }]}


def get_subnet_group_side_effect():
    return {
        "DBSubnetGroups": [
            {
                "DBSubnetGroupName": DOCDB_SUBNET_GROUP_NAME,
                "DBSubnetGroupDescription": "DocumentDB cluster subnet group",
                "VpcId": "vpc-091947ce4f16248b5",
                "SubnetGroupStatus": "Complete",
                "Subnets": [
                    {
                        "SubnetIdentifier": "subnet-0be28e5a030e46966",
                        "SubnetAvailabilityZone": {
                            "Name": "us-east-1a"
                        },
                        "SubnetStatus": "Active"
                    },
                    {
                        "SubnetIdentifier": "subnet-08e4a8215ce4dc164",
                        "SubnetAvailabilityZone": {
                            "Name": "us-east-1b"
                        },
                        "SubnetStatus": "Active"
                    }
                ],
                "DBSubnetGroupArn": "arn:aws:rds:us-east-2:435978235099:subgrp:docdbclustersubnetgroup-bvhpczyfghso"
            }
        ]
    }


DOCDB_INSTANCES = {
    'DBInstances': [
        {
            'DBInstanceStatus': DOCDB_INSTANCE_STATUS
        }
    ]
}


def get_unavailable_instance_side_effect(DBInstanceIdentifier):
    response = copy.deepcopy(DESCRIBE_DB_INSTANCES_RESPONSE)
    response['DBInstances'][0]['DBInstanceStatus'] = 'unavailable'
    return response


def get_scale_up_instances_side_effect(amount):
    response = []
    for _ in range(amount):
        rnd = str(uuid.uuid4()).split('-')[-1]
        response.append(f'{DOCDB_CLUSTER_ID}-{rnd}')
    return {'DBInstancesIdentifiers': response}


@pytest.mark.unit_test
class TestDocDBUtil(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('boto3.client')
        self.client = self.patcher.start()
        self.mock_docdb = MagicMock()
        self.side_effect_map = {
            'docdb': self.mock_docdb
        }
        self.client.side_effect = lambda service_name, config=None: self.side_effect_map.get(service_name)

        self.mock_docdb.describe_db_instances.return_value = DOCDB_INSTANCES

    def tearDown(self):
        self.patcher.stop()

    # Test count_cluster_instances
    def test_count_cluster_instances(self):
        events = {
            'DbClusterInstances': get_docdb_clusters_side_effect(3)['DBClusters'][0]['DBClusterMembers']
        }
        response = count_cluster_instances(events, None)
        self.assertEqual(3, response['DbClusterInstancesNumber'])

    def test_count_cluster_instances_empty(self):
        events = {
            'DbClusterInstances': []
        }
        response = count_cluster_instances(events, None)
        self.assertEqual(0, response['DbClusterInstancesNumber'])

    def test_count_cluster_instances_missing(self):
        events = {}
        self.assertRaises(Exception, count_cluster_instances, events, None)

    # Test verify_db_instance_exist

    def test_verify_db_instance_exist(self):
        events = {
            'DBInstanceIdentifier': DOCDB_INSTANCE_ID,
            'DBClusterIdentifier': DOCDB_CLUSTER_ID,
        }
        response = verify_db_instance_exist(events, None)
        self.mock_docdb.describe_db_instances.assert_called_once_with(
            DBInstanceIdentifier=DOCDB_INSTANCE_ID,
            Filters=[
                {
                    'Name': 'db-cluster-id',
                    'Values': [DOCDB_CLUSTER_ID]
                },
            ]
        )
        self.assertEqual(DOCDB_INSTANCE_STATUS, response[DOCDB_INSTANCE_ID])

    def test_verify_db_instance_exist_missing_instance_id(self):
        events = {
            'DBClusterIdentifier': DOCDB_CLUSTER_ID,
        }
        self.assertRaises(Exception, verify_db_instance_exist, events, None)

    def test_verify_db_instance_exist_missing_cluster_id(self):
        events = {
            'DBInstanceIdentifier': DOCDB_INSTANCE_ID,
        }
        self.assertRaises(Exception, verify_db_instance_exist, events, None)

    def test_verify_db_instance_exist_not_found(self):
        events = {
            'DBInstanceIdentifier': DOCDB_INSTANCE_ID,
            'DBClusterIdentifier': DOCDB_CLUSTER_ID,
        }
        self.mock_docdb.describe_db_instances.side_effect = MagicMock(side_effect=Exception('DBInstanceNotFound'))
        self.assertRaises(Exception, verify_db_instance_exist, events, None)
        self.mock_docdb.describe_db_instances.assert_called_once_with(
            DBInstanceIdentifier=DOCDB_INSTANCE_ID,
            Filters=[
                {
                    'Name': 'db-cluster-id',
                    'Values': [DOCDB_CLUSTER_ID]
                },
            ]
        )

    # Test verify_cluster_instances

    def test_verify_cluster_instances(self):
        events = {
            'DBClusterIdentifier': DOCDB_CLUSTER_ID,
            'BeforeDbClusterInstancesNumber': 2
        }

        self.mock_docdb.describe_db_clusters.return_value = get_docdb_clusters_side_effect(3)
        response = verify_cluster_instances(events, None)
        self.mock_docdb.describe_db_clusters.assert_called_once_with(DBClusterIdentifier=DOCDB_CLUSTER_ID)
        self.assertEqual(3, response['DbClusterInstancesNumber'])

    def test_verify_cluster_instances_not_changed(self):
        events = {
            'DBClusterIdentifier': DOCDB_CLUSTER_ID,
            'BeforeDbClusterInstancesNumber': 3
        }

        self.mock_docdb.describe_db_clusters.return_value = get_docdb_clusters_side_effect(3)
        self.assertRaises(Exception, verify_cluster_instances, events, None)
        self.mock_docdb.describe_db_clusters.assert_called_once_with(DBClusterIdentifier=DOCDB_CLUSTER_ID)

    def test_verify_cluster_instances_missing_id(self):
        events = {}
        self.assertRaises(Exception, verify_cluster_instances, events, None)

    def test_verify_cluster_instances_missing_old_value(self):
        events = {
            'DBClusterIdentifier': DOCDB_CLUSTER_ID
        }
        self.assertRaises(Exception, verify_cluster_instances, events, None)

    # Test get_cluster_az
    def test_get_cluster_az_empty_events(self):
        events = {}
        self.assertRaises(Exception, get_cluster_az, events, None)

    def test_get_cluster_az_valid_cluster(self):
        events = {
            'DBClusterIdentifier': DOCDB_CLUSTER_ID
        }
        self.mock_docdb.describe_db_clusters.return_value = get_describe_db_cluster_side_effect()
        self.mock_docdb.describe_db_subnet_groups.return_value = get_subnet_group_side_effect()
        response = get_cluster_az(events, None)
        self.assertEqual(['us-east-1a', 'us-east-1b'], response['cluster_azs'])

    def test_get_cluster_az_not_existing_cluster(self):
        events = {
            'DBClusterIdentifier': 'NOT_EXISTING_CLUSTER_ID'
        }
        self.mock_docdb.describe_db_clusters.return_value = {}
        self.assertRaises(Exception, get_cluster_az, events, None)

    # Test create_new_instance
    def test_create_new_instance_az_from_AvailabilityZone(self):
        events = {
            'AvailabilityZone': DOCDB_AZ,
            'DBInstanceIdentifier': 'id1',
            'DBInstanceClass': DOCDB_INSTANCE_CLASS,
            'Engine': DOCDB_ENGINE,
            'DBClusterIdentifier': DOCDB_CLUSTER_ID
        }
        self.mock_docdb.create_db_instance.return_value = get_create_db_instance_side_effect(DOCDB_AZ)
        response = create_new_instance(events, None)
        self.assertEqual({'instance_az': DOCDB_AZ}, response)
        self.mock_docdb.create_db_instance.assert_called_once_with(
            AvailabilityZone=DOCDB_AZ,
            DBInstanceIdentifier='id1',
            DBInstanceClass=DOCDB_INSTANCE_CLASS,
            Engine=DOCDB_ENGINE,
            DBClusterIdentifier=DOCDB_CLUSTER_ID
        )

    def test_create_new_instance_az_from_DBClusterAZs(self):
        events = {
            'DBClusterAZs': [DOCDB_AZ],
            'DBInstanceIdentifier': 'id1',
            'DBInstanceClass': DOCDB_INSTANCE_CLASS,
            'Engine': DOCDB_ENGINE,
            'DBClusterIdentifier': DOCDB_CLUSTER_ID
        }
        self.mock_docdb.create_db_instance.return_value = get_create_db_instance_side_effect(DOCDB_AZ)
        response = create_new_instance(events, None)
        self.assertEqual({'instance_az': DOCDB_AZ}, response)
        self.mock_docdb.create_db_instance.assert_called_once_with(
            AvailabilityZone=DOCDB_AZ,
            DBInstanceIdentifier='id1',
            DBInstanceClass=DOCDB_INSTANCE_CLASS,
            Engine=DOCDB_ENGINE,
            DBClusterIdentifier=DOCDB_CLUSTER_ID
        )

    def test_create_new_instance_missing_az(self):
        events = {
            'DBInstanceIdentifier': 'id1',
            'DBInstanceClass': DOCDB_INSTANCE_CLASS,
            'Engine': DOCDB_ENGINE,
            'DBClusterIdentifier': DOCDB_CLUSTER_ID
        }
        self.mock_docdb.create_db_instance.return_value = get_create_db_instance_side_effect(DOCDB_AZ)
        self.assertRaises(Exception, create_new_instance, events, None)

    def test_create_new_instance_missing_instance_identifier(self):
        events = {
            'DBClusterAZs': [DOCDB_AZ],
            'DBInstanceClass': DOCDB_INSTANCE_CLASS,
            'Engine': DOCDB_ENGINE,
            'DBClusterIdentifier': DOCDB_CLUSTER_ID
        }
        self.mock_docdb.create_db_instance.return_value = get_create_db_instance_side_effect(DOCDB_AZ)
        self.assertRaises(Exception, create_new_instance, events, None)

    def test_create_new_instance_missing_cluster_identifier(self):
        events = {
            'DBClusterAZs': [DOCDB_AZ],
            'DBInstanceIdentifier': 'id1',
            'DBInstanceClass': DOCDB_INSTANCE_CLASS,
            'Engine': DOCDB_ENGINE,
        }
        self.mock_docdb.create_db_instance.return_value = get_create_db_instance_side_effect(DOCDB_AZ)
        self.assertRaises(Exception, create_new_instance, events, None)

    def test_create_new_instance_missing_engine(self):
        events = {
            'DBClusterAZs': [DOCDB_AZ],
            'DBInstanceIdentifier': 'id1',
            'DBInstanceClass': DOCDB_INSTANCE_CLASS,
            'DBClusterIdentifier': DOCDB_CLUSTER_ID
        }
        self.mock_docdb.create_db_instance.return_value = get_create_db_instance_side_effect(DOCDB_AZ)
        self.assertRaises(Exception, create_new_instance, events, None)

    def test_create_new_instance_missing_instance_class(self):
        events = {
            'DBClusterAZs': [DOCDB_AZ],
            'DBInstanceIdentifier': 'id1',
            'Engine': DOCDB_ENGINE,
            'DBClusterIdentifier': DOCDB_CLUSTER_ID
        }
        self.mock_docdb.create_db_instance.return_value = get_create_db_instance_side_effect(DOCDB_AZ)
        self.assertRaises(Exception, create_new_instance, events, None)

    # Test get_recovery_time_input
    def test_get_recovery_time_input_latest_date(self):
        events = {
            'RestoreToDate': 'latest',
            'DBClusterIdentifier': DOCDB_CLUSTER_ID
        }
        date = datetime(2020, 1, 1, 0, 0)
        self.mock_docdb.describe_db_clusters.return_value = get_docdb_clusters_restore_date_side_effect(date)
        response = get_recovery_point_input(events, None)
        self.assertEqual({'RecoveryPoint': '2020-01-01T00:00:00'}, response)
        self.mock_docdb.describe_db_clusters.assert_called_once_with(
            DBClusterIdentifier=DOCDB_CLUSTER_ID
        )

    def test_get_recovery_time_input_actual_date(self):
        events = {
            'RestoreToDate': '2020-01-01T00:00:00',
            'DBClusterIdentifier': DOCDB_CLUSTER_ID
        }
        self.mock_docdb.describe_db_clusters.return_value = get_docdb_clusters_restore_date_side_effect('')
        response = get_recovery_point_input(events, None)
        self.assertEqual({'RecoveryPoint': '2020-01-01T00:00:00'}, response)

    def test_get_recovery_time_input_missing_restore_to_date(self):
        events = {
            'DBClusterIdentifier': DOCDB_CLUSTER_ID
        }
        self.assertRaises(Exception, get_recovery_point_input, events, None)

    def test_get_recovery_time_input_missing_db_cluster_identifier(self):
        events = {
            'RestoreToDate': '2020-01-01T00:00:00',
        }
        self.assertRaises(Exception, get_recovery_point_input, events, None)

    # Test backup_cluster_instances_type
    def test_backup_cluster_instances_type(self):
        cluster_members = [{
            'DBInstanceIdentifier': 'Instance1',
            'IsClusterWriter': True
        }, {
            'DBInstanceIdentifier': 'Instance2',
            'IsClusterWriter': False
        }]
        events = {'DBClusterInstances': cluster_members}
        self.mock_docdb.describe_db_instances.side_effect = [
            {'DBInstances': [
                {
                    'DBInstanceIdentifier': 'Instance1',
                    'DBInstanceClass': DOCDB_INSTANCE_CLASS,
                    'Engine': DOCDB_ENGINE,
                    'AvailabilityZone': DOCDB_AZ
                }
            ]},
            {'DBInstances': [
                {
                    'DBInstanceIdentifier': 'Instance2',
                    'DBInstanceClass': DOCDB_INSTANCE_CLASS,
                    'Engine': DOCDB_ENGINE,
                    'AvailabilityZone': DOCDB_AZ
                }
            ]}
        ]

        response = backup_cluster_instances_type(events, None)
        self.assertEqual({
            'DBClusterInstancesMetadata': {
                'Instance1': {
                    'DBInstanceClass': DOCDB_INSTANCE_CLASS,
                    'Engine': DOCDB_ENGINE,
                    'AvailabilityZone': DOCDB_AZ
                },
                'Instance2': {
                    'DBInstanceClass': DOCDB_INSTANCE_CLASS,
                    'Engine': DOCDB_ENGINE,
                    'AvailabilityZone': DOCDB_AZ
                }}
        }, response)
        calls = [
            call(DBInstanceIdentifier='Instance1'),
            call(DBInstanceIdentifier='Instance2')
        ]
        self.mock_docdb.describe_db_instances.assert_has_calls(calls)

    def test_backup_cluster_instances_type_empty_events(self):
        events = {}
        self.assertRaises(Exception, backup_cluster_instances_type, events, None)

    # Test restore_to_point_in_time
    def test_restore_to_point_in_time_restore_date_latest(self):
        vpc_security_group_ids = ['vpc1', 'vpc2']
        events = {
            'DBClusterIdentifier': DOCDB_CLUSTER_ID,
            'RestoreToDate': 'latest',
            'VpcSecurityGroupIds': vpc_security_group_ids
        }
        self.mock_docdb.describe_db_clusters.return_value = DESCRIBE_DB_CLUSTER_RESPONSE
        response = restore_to_point_in_time(events, None)
        new_cluster_identifier = DOCDB_CLUSTER_ID + '-restored'
        self.mock_docdb.restore_db_cluster_to_point_in_time.assert_called_once_with(
            DBClusterIdentifier=new_cluster_identifier,
            SourceDBClusterIdentifier=DOCDB_CLUSTER_ID,
            DBSubnetGroupName=DBSUBNET_GROUP,
            UseLatestRestorableTime=True,
            VpcSecurityGroupIds=vpc_security_group_ids
        )
        self.assertEqual({'RestoredClusterIdentifier': new_cluster_identifier}, response)

    def test_restore_to_point_in_time_actual_restore_date(self):
        vpc_security_group_ids = ['vpc1', 'vpc2']
        date = '2020-01-01T00:00:00Z'
        events = {
            'DBClusterIdentifier': DOCDB_CLUSTER_ID,
            'RestoreToDate': date,
            'VpcSecurityGroupIds': vpc_security_group_ids
        }
        self.mock_docdb.describe_db_clusters.return_value = DESCRIBE_DB_CLUSTER_RESPONSE
        response = restore_to_point_in_time(events, None)
        new_cluster_identifier = DOCDB_CLUSTER_ID + '-restored'
        self.mock_docdb.restore_db_cluster_to_point_in_time.assert_called_once_with(
            DBClusterIdentifier=new_cluster_identifier,
            SourceDBClusterIdentifier=DOCDB_CLUSTER_ID,
            DBSubnetGroupName=DBSUBNET_GROUP,
            RestoreToTime=datetime.strptime(date, "%Y-%m-%dT%H:%M:%S%z"),
            VpcSecurityGroupIds=vpc_security_group_ids
        )
        self.assertEqual({'RestoredClusterIdentifier': new_cluster_identifier}, response)

    def test_restore_to_point_in_time_empty_events(self):
        events = {}
        self.assertRaises(Exception, restore_to_point_in_time, events, None)

    # Test restore_db_cluster_instances
    def test_restore_db_cluster_instances_same_cluster_azs(self):
        events = {
            'BackupDbClusterInstancesCountValue': [
                {
                    'DBInstanceIdentifier': 'Instance1',
                    'IsClusterWriter': True
                }, {
                    'DBInstanceIdentifier': 'Instance2',
                    'IsClusterWriter': False
                }
            ],
            'DBClusterIdentifier': DOCDB_CLUSTER_ID,
            'DBClusterInstancesMetadata': {
                'Instance1': {
                    'DBInstanceClass': DOCDB_INSTANCE_CLASS,
                    'Engine': DOCDB_ENGINE,
                    'AvailabilityZone': 'us-east-1a'
                },
                'Instance2': {
                    'DBInstanceClass': DOCDB_INSTANCE_CLASS,
                    'Engine': DOCDB_ENGINE,
                    'AvailabilityZone': 'us-east-1b'
                }
            }
        }
        self.mock_docdb.describe_db_clusters.return_value = {
            'DBClusters': [
                {
                    'DBClusterIdentifier': DOCDB_CLUSTER_ID,
                    'AvailabilityZones': ['us-east-1a', 'us-east-1b']
                }
            ]
        }
        response = restore_db_cluster_instances(events, None)
        calls = [
            call(
                DBInstanceIdentifier='Instance1-restored',
                DBInstanceClass=DOCDB_INSTANCE_CLASS,
                Engine=DOCDB_ENGINE,
                DBClusterIdentifier=DOCDB_CLUSTER_ID,
                AvailabilityZone='us-east-1a',
                PromotionTier=1
            ),
            call(
                DBInstanceIdentifier='Instance2-restored',
                DBInstanceClass=DOCDB_INSTANCE_CLASS,
                Engine=DOCDB_ENGINE,
                DBClusterIdentifier=DOCDB_CLUSTER_ID,
                AvailabilityZone='us-east-1b',
                PromotionTier=2
            )
        ]
        self.mock_docdb.create_db_instance.assert_has_calls(calls)
        self.assertEqual(['Instance1-restored', 'Instance2-restored'], response)

    def test_restore_db_cluster_instances_different_cluster_azs(self):
        events = {
            'BackupDbClusterInstancesCountValue': [
                {
                    'DBInstanceIdentifier': 'Instance1',
                    'IsClusterWriter': True
                }, {
                    'DBInstanceIdentifier': 'Instance2',
                    'IsClusterWriter': False
                }, {
                    'DBInstanceIdentifier': 'Instance3',
                    'IsClusterWriter': False
                }
            ],
            'DBClusterIdentifier': DOCDB_CLUSTER_ID,
            'DBClusterInstancesMetadata': {
                'Instance1': {
                    'DBInstanceClass': DOCDB_INSTANCE_CLASS,
                    'Engine': DOCDB_ENGINE,
                    'AvailabilityZone': 'us-east-1a'
                },
                'Instance2': {
                    'DBInstanceClass': DOCDB_INSTANCE_CLASS,
                    'Engine': DOCDB_ENGINE,
                    'AvailabilityZone': 'us-east-1b'
                },
                'Instance3': {
                    'DBInstanceClass': DOCDB_INSTANCE_CLASS,
                    'Engine': DOCDB_ENGINE,
                    'AvailabilityZone': 'us-east-1c'
                }
            }
        }
        self.mock_docdb.describe_db_clusters.return_value = {
            'DBClusters': [
                {
                    'DBClusterIdentifier': DOCDB_CLUSTER_ID,
                    'AvailabilityZones': ['us-east-1a', 'us-east-1d', 'us-east-1f']
                }
            ]
        }
        response = restore_db_cluster_instances(events, None)
        calls = [
            call(
                DBInstanceIdentifier='Instance1-restored',
                DBInstanceClass=DOCDB_INSTANCE_CLASS,
                Engine=DOCDB_ENGINE,
                DBClusterIdentifier=DOCDB_CLUSTER_ID,
                AvailabilityZone='us-east-1a',
                PromotionTier=1
            ),
            call(
                DBInstanceIdentifier='Instance2-restored',
                DBInstanceClass=DOCDB_INSTANCE_CLASS,
                Engine=DOCDB_ENGINE,
                DBClusterIdentifier=DOCDB_CLUSTER_ID,
                AvailabilityZone='us-east-1d',
                PromotionTier=2
            ),
            call(
                DBInstanceIdentifier='Instance3-restored',
                DBInstanceClass=DOCDB_INSTANCE_CLASS,
                Engine=DOCDB_ENGINE,
                DBClusterIdentifier=DOCDB_CLUSTER_ID,
                AvailabilityZone='us-east-1f',
                PromotionTier=2
            )
        ]
        self.mock_docdb.create_db_instance.assert_has_calls(calls)
        self.assertEqual(['Instance1-restored', 'Instance2-restored', 'Instance3-restored'], response)

    def test_create_db_instance_empty_events(self):
        self.assertRaises(Exception, restore_db_cluster_instances, {}, None)

    # Test rename_replaced_db_cluster
    def test_rename_replaced_db_cluster(self):
        events = {
            'DBClusterIdentifier': DOCDB_CLUSTER_ID
        }
        response = rename_replaced_db_cluster(events, None)
        self.mock_docdb.modify_db_cluster.assert_called_once_with(
            DBClusterIdentifier=DOCDB_CLUSTER_ID,
            NewDBClusterIdentifier=DOCDB_CLUSTER_ID + '-replaced',
            ApplyImmediately=True
        )
        self.assertEqual({'ReplacedClusterIdentifier': DOCDB_CLUSTER_ID + '-replaced'}, response)

    def test_rename_replaced_db_cluster_empty_events(self):
        self.assertRaises(Exception, rename_replaced_db_cluster, {}, None)

    # Test rename_replaced_db_instances
    def test_rename_replaced_db_instances(self):
        events = {
            'BackupDbClusterInstancesCountValue': [
                {
                    'DBInstanceIdentifier': 'Instance1',
                    'IsClusterWriter': True
                }, {
                    'DBInstanceIdentifier': 'Instance2',
                    'IsClusterWriter': False
                }
            ],
        }
        response = rename_replaced_db_instances(events, None)
        calls = [
            call(
                DBInstanceIdentifier='Instance1',
                ApplyImmediately=True,
                NewDBInstanceIdentifier='Instance1-replaced',
            ),
            call(
                DBInstanceIdentifier='Instance2',
                ApplyImmediately=True,
                NewDBInstanceIdentifier='Instance2-replaced',
            )
        ]
        self.mock_docdb.modify_db_instance.assert_has_calls(calls)
        self.assertEqual(['Instance1-replaced', 'Instance2-replaced'], response)

    def test_rename_replaced_db_instances_empty_events(self):
        self.assertRaises(Exception, rename_replaced_db_instances, {}, None)

    # Test rename_restored_db_instances
    def test_rename_restored_db_instances(self):
        events = {
            'RestoredInstancesIdentifiers': ['Instance1-restored', 'Instance2-restored']
        }
        response = rename_restored_db_instances(events, None)
        calls = [
            call(
                DBInstanceIdentifier='Instance1-restored',
                ApplyImmediately=True,
                NewDBInstanceIdentifier='Instance1'
            ),
            call(
                DBInstanceIdentifier='Instance2-restored',
                ApplyImmediately=True,
                NewDBInstanceIdentifier='Instance2'
            )
        ]
        self.mock_docdb.modify_db_instance.assert_has_calls(calls)
        self.assertEqual(['Instance1', 'Instance2'], response)

    def test_rename_restored_db_instances_empty_events(self):
        self.assertRaises(Exception, rename_restored_db_instances, {}, None)

    # Test get_latest_snapshot_id
    def test_get_latest_snapshot_id_one_page_three_snapshots(self):
        events = {
            'DBClusterIdentifier': DOCDB_CLUSTER_ID
        }
        number_of_pages = 1
        number_of_snapshots = 3
        latest_snapshot_id = 'Snapshot' + str(number_of_pages * number_of_snapshots)
        self.mock_docdb.get_paginator.side_effect = \
            get_paginate_side_effect(number_of_pages, number_of_snapshots)
        response = get_latest_snapshot_id(events, None)
        self.assertEqual({
            'LatestSnapshotIdentifier': latest_snapshot_id,
            'LatestSnapshotEngine': DOCDB_ENGINE,
            'LatestClusterIdentifier': DOCDB_CLUSTER_ID
        }, response)
        self.mock_docdb.get_paginator.assert_called_once_with('describe_db_cluster_snapshots')

    def test_get_latest_snapshot_id_two_pages(self):
        events = {
            'DBClusterIdentifier': DOCDB_CLUSTER_ID
        }
        number_of_pages = 2
        number_of_snapshots = 4
        latest_snapshot_id = 'Snapshot' + str(number_of_pages * number_of_snapshots)
        self.mock_docdb.get_paginator.side_effect = \
            get_paginate_side_effect(number_of_pages, number_of_snapshots)
        response = get_latest_snapshot_id(events, None)
        self.assertEqual({
            'LatestSnapshotIdentifier': latest_snapshot_id,
            'LatestSnapshotEngine': DOCDB_ENGINE,
            'LatestClusterIdentifier': DOCDB_CLUSTER_ID
        }, response)
        self.mock_docdb.get_paginator.assert_called_once_with('describe_db_cluster_snapshots')

    def test_get_latest_snapshot_id_no_snapshots_available(self):
        events = {
            'DBClusterIdentifier': DOCDB_CLUSTER_ID
        }
        number_of_pages = 0
        number_of_snapshots = 0

        self.mock_docdb.get_paginator.side_effect = \
            get_paginate_side_effect(number_of_pages, number_of_snapshots)
        self.assertRaises(Exception, get_latest_snapshot_id, events, None)
        self.mock_docdb.get_paginator.assert_called_once_with('describe_db_cluster_snapshots')

    def test_get_latest_snapshot_id_empty_events(self):
        self.assertRaises(Exception, get_latest_snapshot_id, {}, None)

    def test_restore_db_cluster_no_snapshot_identifier(self):
        events = {
            'DBClusterIdentifier': DOCDB_CLUSTER_ID,
            'DBSnapshotIdentifier': '',
            'LatestSnapshotIdentifier': 'Snapshot3',
            'LatestSnapshotEngine': DOCDB_ENGINE,
            'AvailabilityZones': [DOCDB_AZ]
        }
        self.mock_docdb.describe_db_clusters.return_value = DESCRIBE_DB_CLUSTER_RESPONSE
        response = restore_db_cluster(events, None)
        cluster_id = DOCDB_CLUSTER_ID + '-restored-from-backup'
        self.mock_docdb.restore_db_cluster_from_snapshot.assert_called_once_with(
            DBClusterIdentifier=cluster_id,
            SnapshotIdentifier='Snapshot3',
            DBSubnetGroupName=DBSUBNET_GROUP,
            VpcSecurityGroupIds=[SG_ID],
            Engine=DOCDB_ENGINE,
            AvailabilityZones=[DOCDB_AZ]
        )
        self.assertEqual({'RestoredClusterIdentifier': cluster_id}, response)

    def test_restore_db_cluster_snapshot_identifier_latest(self):
        events = {
            'DBClusterIdentifier': DOCDB_CLUSTER_ID,
            'DBSnapshotIdentifier': 'latest',
            'LatestSnapshotIdentifier': 'Snapshot3',
            'LatestSnapshotEngine': DOCDB_ENGINE,
            'AvailabilityZones': [DOCDB_AZ]
        }
        self.mock_docdb.describe_db_clusters.return_value = DESCRIBE_DB_CLUSTER_RESPONSE
        response = restore_db_cluster(events, None)
        cluster_id = DOCDB_CLUSTER_ID + '-restored-from-backup'
        self.mock_docdb.restore_db_cluster_from_snapshot.assert_called_once_with(
            DBClusterIdentifier=cluster_id,
            SnapshotIdentifier='Snapshot3',
            DBSubnetGroupName=DBSUBNET_GROUP,
            VpcSecurityGroupIds=[SG_ID],
            Engine=DOCDB_ENGINE,
            AvailabilityZones=[DOCDB_AZ]
        )
        self.assertEqual({'RestoredClusterIdentifier': cluster_id}, response)

    def test_restore_db_cluster_actual_snapshot_identifier(self):
        events = {
            'DBClusterIdentifier': DOCDB_CLUSTER_ID,
            'DBSnapshotIdentifier': 'Snapshot2',
            'LatestSnapshotIdentifier': 'Snapshot3',
            'LatestSnapshotEngine': DOCDB_ENGINE,
            'AvailabilityZones': [DOCDB_AZ]
        }
        self.mock_docdb.describe_db_clusters.return_value = DESCRIBE_DB_CLUSTER_RESPONSE
        response = restore_db_cluster(events, None)
        cluster_id = DOCDB_CLUSTER_ID + '-restored-from-backup'
        self.mock_docdb.restore_db_cluster_from_snapshot.assert_called_once_with(
            DBClusterIdentifier=cluster_id,
            SnapshotIdentifier='Snapshot2',
            DBSubnetGroupName=DBSUBNET_GROUP,
            VpcSecurityGroupIds=[SG_ID],
            Engine=DOCDB_ENGINE,
            AvailabilityZones=[DOCDB_AZ]
        )
        self.assertEqual({'RestoredClusterIdentifier': cluster_id}, response)

    def test_restore_db_cluster_wrong_clusterid(self):
        events = {
            'DBClusterIdentifier': DOCDB_CLUSTER_ID,
            'DBSnapshotIdentifier': 'Snapshot2',
            'LatestSnapshotIdentifier': 'Snapshot3',
            'LatestSnapshotEngine': DOCDB_ENGINE,
            'AvailabilityZones': [DOCDB_AZ]
        }

        self.mock_docdb.describe_db_clusters.return_value = {"DBClusters": []}
        with pytest.raises(AssertionError) as assertion_error:
            restore_db_cluster(events, None)
        self.mock_docdb.restore_db_cluster_from_snapshot.assert_not_called()
        self.assertEqual(f'No db cluster found with id: {DOCDB_CLUSTER_ID}', str(assertion_error.value))

    def test_restore_db_cluster_empty_events(self):
        self.assertRaises(Exception, restore_db_cluster, {}, None)

    def test_restore_security_group_ids_not_all_arguments(self):
        assert_having_all_not_empty_arguments_in_events(Exception, restore_security_group_ids,
                                                        ['VpcSecurityGroupIds', 'DBClusterIdentifier'])

    def test_restore_security_group_ids(self):
        self.mock_docdb.modify_db_cluster.return_value = MODIFY_DB_CLUSTER_RESPONSE
        sgs = [SG_ID]
        events = {
            'DBClusterIdentifier': DOCDB_CLUSTER_ID,
            'VpcSecurityGroupIds': sgs,
        }
        response = restore_security_group_ids(events, None)
        self.mock_docdb.modify_db_cluster.assert_called_once_with(
            DBClusterIdentifier=DOCDB_CLUSTER_ID,
            VpcSecurityGroupIds=sgs
        )
        self.assertEqual({'VpcSecurityGroupIds': sgs}, response)

    def test_get_db_cluster_properties_not_all_arguments(self):
        assert_having_all_not_empty_arguments_in_events(Exception, get_db_cluster_properties,
                                                        ['DBClusterIdentifier'])

    def test_get_db_cluster_properties(self):
        self.mock_docdb.describe_db_clusters.return_value = DESCRIBE_DB_CLUSTER_RESPONSE
        sgs = [SG_ID]
        events = {
            'DBClusterIdentifier': DOCDB_CLUSTER_ID,
        }
        response = get_db_cluster_properties(events, None)
        self.mock_docdb.describe_db_clusters.assert_called_once_with(
            DBClusterIdentifier=DOCDB_CLUSTER_ID
        )
        self.assertEqual({'DBInstanceIdentifiers': [DOCDB_INSTANCE_ID],
                          'DBSubnetGroup': DBSUBNET_GROUP,
                          'VpcSecurityGroupIds': sgs},
                         response)

    def test_wait_for_available_instances_not_all_arguments(self):
        assert_having_all_not_empty_arguments_in_events(Exception, wait_for_available_instances,
                                                        ['DBInstanceIdentifiers', 'WaitTimeout', ])

    def test_wait_for_available_instances(self):
        self.mock_docdb.describe_db_instances.return_value = DESCRIBE_DB_INSTANCES_RESPONSE

        events = {
            'DBInstanceIdentifiers': [DOCDB_INSTANCE_ID],
            'WaitTimeout': 5
        }
        wait_for_available_instances(events, None)
        self.mock_docdb.describe_db_instances.assert_called_with(
            DBInstanceIdentifier=DOCDB_INSTANCE_ID
        )

    @patch('time.sleep')
    def test_wait_for_available_instances_timeout(self, patched_sleep):
        mock_sleep = MockSleep()
        patched_sleep.side_effect = mock_sleep.sleep
        self.mock_docdb.describe_db_instances.side_effect = get_unavailable_instance_side_effect
        self.assertRaises(TimeoutError, wait_for_available_instances,
                          {
                              'DBInstanceIdentifiers': [DOCDB_INSTANCE_ID],
                              'WaitTimeout': 21
                          }, None)
        self.mock_docdb.describe_db_instances.assert_called_with(
            DBInstanceIdentifier=DOCDB_INSTANCE_ID
        )

    # Test get_current_db_instance_class
    def test_get_current_db_instance_custom_class(self):
        events = {
            'DBClusterIdentifier': DOCDB_CLUSTER_ID,
            'DBInstanceClass': DOCDB_INSTANCE_CLASS
        }
        response = get_current_db_instance_class(events, None)
        self.assertEqual({
            'DBInstanceClass': DOCDB_INSTANCE_CLASS
        }, response)

    def test_get_current_db_instance_current_class(self):
        events = {
            'DBClusterIdentifier': DOCDB_CLUSTER_ID,
            'DBInstanceClass': 'current'
        }
        self.mock_docdb.get_paginator.side_effect = \
            get_paginated_instances_side_effect()
        response = get_current_db_instance_class(events, None)
        self.assertEqual({
            'DBInstanceClass': DOCDB_INSTANCE_CLASS
        }, response)
        self.mock_docdb.get_paginator.assert_called_once_with('describe_db_instances')

    def test_get_current_db_instance_empty_class(self):
        events = {
            'DBClusterIdentifier': DOCDB_CLUSTER_ID,
            'DBInstanceClass': ''
        }
        self.assertRaises(KeyError, get_current_db_instance_class, events, None)

    def test_get_current_db_instance_empty_cluster_id(self):
        events = {
            'DBClusterIdentifier': None,
            'DBInstanceClass': DOCDB_INSTANCE_CLASS
        }
        self.assertRaises(Exception, get_current_db_instance_class, events, None)

    def test_get_current_db_instance_no_instances_found(self):
        events = {
            'DBClusterIdentifier': 'something',
            'DBInstanceClass': 'current'
        }
        self.assertRaises(Exception, get_current_db_instance_class, events, None)

    # Test scale up cluster
    def test_scale_up_cluster_6_instances(self):
        events = {
            'DBInstanceIdentifierPrefix': DOCDB_CLUSTER_ID,
            'NumberOfInstancesToCreate': 6,
            'DBInstanceClass': DOCDB_INSTANCE_CLASS,
            'DBClusterEngine': DOCDB_ENGINE,
            'DBClusterIdentifier': DOCDB_CLUSTER_ID
        }
        self.mock_docdb.scale_up_instances.return_value = get_scale_up_instances_side_effect(6)
        response = scale_up_cluster(events, None)
        self.assertEqual(6, len(response['DBInstancesIdentifiers']))

    def test_scale_up_cluster_0_instances(self):
        events = {
            'DBInstanceIdentifierPrefix': DOCDB_CLUSTER_ID,
            'NumberOfInstancesToCreate': 0,
            'DBInstanceClass': DOCDB_INSTANCE_CLASS,
            'DBClusterEngine': DOCDB_ENGINE,
            'DBClusterIdentifier': DOCDB_CLUSTER_ID
        }
        self.assertRaises(KeyError, scale_up_cluster, events, None)

    def test_scale_up_cluster_missing_number(self):
        events = {
            'DBInstanceIdentifierPrefix': DOCDB_CLUSTER_ID,
            'DBInstanceClass': DOCDB_INSTANCE_CLASS,
            'DBClusterEngine': DOCDB_ENGINE,
            'DBClusterIdentifier': DOCDB_CLUSTER_ID
        }
        self.assertRaises(KeyError, scale_up_cluster, events, None)

    def test_scale_up_cluster_missing_class(self):
        events = {
            'DBInstanceIdentifierPrefix': DOCDB_CLUSTER_ID,
            'NumberOfInstancesToCreate': 2,
            'DBClusterEngine': DOCDB_ENGINE,
            'DBClusterIdentifier': DOCDB_CLUSTER_ID
        }
        self.assertRaises(KeyError, scale_up_cluster, events, None)

    def test_scale_up_cluster_missing_engine(self):
        events = {
            'DBInstanceIdentifierPrefix': DOCDB_CLUSTER_ID,
            'NumberOfInstancesToCreate': 2,
            'DBInstanceClass': DOCDB_INSTANCE_CLASS,
            'DBClusterIdentifier': DOCDB_CLUSTER_ID
        }
        self.assertRaises(KeyError, scale_up_cluster, events, None)

    def test_scale_up_cluster_missing_cluster_id(self):
        events = {
            'DBInstanceIdentifierPrefix': DOCDB_CLUSTER_ID,
            'NumberOfInstancesToCreate': 6,
            'DBInstanceClass': DOCDB_INSTANCE_CLASS,
            'DBClusterEngine': DOCDB_ENGINE
        }
        self.assertRaises(KeyError, scale_up_cluster, events, None)

    # Test delete list of instances
    def test_delete_list_of_instances(self):
        instance_identifiers = [
            f'{DOCDB_CLUSTER_ID}-instance-1',
            f'{DOCDB_CLUSTER_ID}-instance-2'
        ]
        self.mock_docdb.delete_list_of_instances.return_value = DELETE_LIST_OF_INSTANCES_RESPONSE
        response = delete_list_of_instances(instance_identifiers)
        self.assertListEqual(DELETE_LIST_OF_INSTANCES_RESPONSE, response)

    def test_delete_list_of_instances_empty_list(self):
        instance_identifiers = []
        response = delete_list_of_instances(instance_identifiers)
        self.assertIsNone(response)
