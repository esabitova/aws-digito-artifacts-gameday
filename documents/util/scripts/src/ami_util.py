import boto3


def get_ami_id(events, context):
    ec2 = boto3.client('ec2')
    ec2_images = ec2.describe_images(
        Filters=[{
            'Name': 'name',
            'Values': [events['AmiName']]
        }])
    output = {}
    output['AmiId'] = ec2_images['Images'][0]['ImageId']
    return output
