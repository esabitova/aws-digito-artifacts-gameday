from adk.src.adk.parent_steps.wait_for_resource_step import WaitForResourceStep


def get_wait_for_instance_start():
    return WaitForResourceStep(
        name='WaitForInstanceStart',
        description='Waits for instance to start running',
        service='ec2',
        camel_case_api='DescribeInstances',
        desired_values=['running', 'going'],
        selector='$.Reservations[0].Instances[0].State.Name',
        api_params={
            'Filters': [{
                'Name': 'instance-id',
                'Values': ['{{ InstanceId }}']
            }]
        }
    )
