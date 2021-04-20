import boto3
from botocore.config import Config


def get_ami_id(events, context):
    config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
    ec2 = boto3.client('ec2', config=config)
    ec2_images = ec2.describe_images(
        Filters=[{
            'Name': 'name',
            'Values': [events['AmiName']]
        }])
    output = {}
    output['AmiId'] = ec2_images['Images'][0]['ImageId']
    return output
