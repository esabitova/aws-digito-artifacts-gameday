from adk.src.adk.domain.data_type import DataType
from adk.src.adk.domain.output import Output
from adk.src.adk.parent_steps.aws_api_step import AwsApiStep


def get_ec2_describe_instances():
    return AwsApiStep(
        name='Ec2DescribeInstances',
        description='Describes EC2 Instance',
        service='ec2',
        camel_case_api='DescribeInstances',
        api_params={
            'Filters': [{
                'Name': 'instance-id',
                'Values': ['{{ InstanceId }}']
            }]
        },
        outputs=[
            Output('InstanceType', DataType.String, '$.Reservations[0].Instances[0].InstanceType'),
            Output('State', DataType.String, '$.Reservations[0].Instances[0].State.Name')
        ]
    )
