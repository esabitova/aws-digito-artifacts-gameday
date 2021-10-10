from adk.src.adk.domain.data_type import DataType
from adk.src.adk.domain.output import Output
from adk.src.adk.parent_steps.automation.aws_api_step import AwsApiStep


def get_ebs_describe_snapshot(snapshot_id_var='EBSSnapshotIdentifier'):
    return AwsApiStep(
        name='EbsDescribeSnapshot',
        description='Get current snapshot information, validate that the state is "completed" by calling'
        + '[DescribeSnapshot](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeSnapshots.html)',
        service='ec2',
        camel_case_api='DescribeSnapshots',
        api_params={
            'Filters': [{
                'Name': 'snapshot-id',
                'Values': ['{{ ' + snapshot_id_var + ' }}']
            }]
        },
        outputs=[
            Output('VolumeId', DataType.String, '$.Snapshots[0].VolumeId'),
            Output('State', DataType.String, '$.Snapshots[0].State')
        ]
    )


def get_ebs_describe_volumes(volume_id_var='EbsDescribeInstance.VolumeId'):
    return AwsApiStep(
        name='EbsDescribeVolumes',
        description='Get volume information '
        + 'calling [DescribeVolumes](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeVolumes.html)',
        service='ec2',
        camel_case_api='DescribeVolumes',
        api_params={
            'Filters': [{
                'Name': 'volume-id',
                'Values': ['{{ ' + volume_id_var + ' }}']
            }]
        },
        outputs=[
            Output('OriginalVolumeType', DataType.String, '$.Volumes[0].VolumeType'),
            Output('OriginalVolumeIOPS', DataType.String, '$.Volumes[0].Iops')
        ]
    )


def get_ebs_create_volume(snapshot_var='EBSSnapshotIdentifier',
                          az_var="TargetAvailabilityZone",
                          volume_var='CalculateIopsAndVolType.TargetVolumeType',
                          iops_var='CalculateIopsAndVolType.TargetVolumeIOPS'):
    return AwsApiStep(
        name='EbsCreateVolume',
        description='Create the new volume by calling '
        + '[CreateVolume](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_CreateVolume.html)',
        service='ec2',
        camel_case_api='CreateVolume',
        api_params={
            'SnapshotId': '{{ ' + snapshot_var + ' }}',
            'AvailabilityZone': '{{ ' + az_var + ' }}',
            'VolumeType': '{{ ' + volume_var + ' }}',
            'Iops': '{{ ' + iops_var + ' }}'
        },
        outputs=[Output('CreatedVolumeId', DataType.String, '$.VolumeId')]
    )


def ebs_describe_instance_volume(instance_id='InstanceIdentifier', device_name='DeviceName'):
    return AwsApiStep(
        name='DescribeInstanceVolume',
        description='Describe volumes by instance and device '
        + '[DescribeVolumes](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeVolumes.html)',
        service='ec2',
        camel_case_api='DescribeVolumes',
        api_params={
            'Filters':
                [{'Name': 'attachment.device', 'Values': ['{{' + device_name + '}}']},
                 {'Name': 'attachment.instance-id', 'Values': ['{{' + instance_id + '}}']}]
        },
        outputs=[Output('VolumeId', DataType.String, '$.Volumes[0].VolumeId'),
                 Output('CurrentSizeGiB', DataType.Integer, '$.Volumes[0].Size')]
    )


def ebs_describe_volume(volume_id='EbsDescribeInstance.VolumeId'):
    return AwsApiStep(
        name='DescribeVolume',
        description='Describe volumes '
        + '[DescribeVolumes](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeVolumes.html)',
        service='ec2',
        camel_case_api='DescribeVolumes',
        api_params={
            'VolumeIds': ['{{ ' + volume_id + ' }}']
        },
        outputs=[Output('CurrentSizeGiB', DataType.Integer, '$.Volumes[0].Size')]
    )


def resize_volume(volume_id='DescribeInstanceVolume.VolumeId', size_gb='SizeGib'):
    return AwsApiStep(
        name='ModifyVolume',
        description='Modify the Volume '
        + '[ModifyVolume](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_ModifyVolume.html)',
        service='ec2',
        camel_case_api='ModifyVolume',
        api_params={
            'VolumeId': '{{ ' + volume_id + ' }}',
            'Size': '{{ ' + size_gb + ' }}'
        },
        outputs=[]
    )
