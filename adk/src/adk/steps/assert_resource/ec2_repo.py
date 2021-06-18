from adk.src.adk.parent_steps.assert_resource_step import AssertResourceStep


def get_assert_instance_start():
    return AssertResourceStep(
        name='AssertInstanceStart',
        description='Waits for instance to start running',
        service='ec2',
        camel_case_api='DescribeInstances',
        selector='$.Reservations[0].Instances[0].State.Name',
        desired_values=['running'],
        api_params={
            'Filters': [{
                'Name': 'instance-id',
                'Values': ['{{ InstanceId }}']
            }]
        }
    )
