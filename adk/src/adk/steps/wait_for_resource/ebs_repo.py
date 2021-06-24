from adk.src.adk.parent_steps.wait_for_resource_step import WaitForResourceStep


def get_wait_for_volume_start(volume_id='CreateEbsVolume.CreatedVolumeId'):
    return WaitForResourceStep(
        name='WaitUntilVolumeAvailable',
        description='Wait until EBS volume status is running',
        service='ec2',
        camel_case_api='DescribeVolumes',
        api_params={
            'Filters': [{
                'Name': 'volume-id',
                'Values': ['{{ ' + volume_id + ' }}']
            }]
        },
        selector='$.Volumes[0].State',
        desired_values=['available']
    )
