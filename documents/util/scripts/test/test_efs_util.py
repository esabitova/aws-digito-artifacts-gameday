def describe_file_systems(fs_id):
    return {'FileSystems': [{
        "OwnerId": "435978235099",
        "CreationToken": "2021-04-13_14.17.16",
        "FileSystemId": fs_id,
        "FileSystemArn": "arn:aws:elasticfilesystem:eu-south-1:435978235099:file-system/" + fs_id,
        "CreationTime": "2021-04-13T17:27:17+03:00",
        "LifeCycleState": "available",
        "NumberOfMountTargets": 0,
        "SizeInBytes": {
            "Value": 24576,
            "Timestamp": "2021-04-14T15:18:54+03:00",
            "ValueInIA": 0,
            "ValueInStandard": 24576
        },
        "PerformanceMode": "generalPurpose",
        "Encrypted": False,
        "ThroughputMode": "bursting",
        "Tags": []
    }]}
