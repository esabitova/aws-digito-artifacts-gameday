import uuid

import boto3
import botocore
from botocore.session import Session


def assume_role_session(role_arn: str, base_session: Session) -> Session:
    """
    Assume role
    :param role_arn: ARN to other role for assuming
    :param base_session: Base boto3 session
    :return: new assumed role
    """
    sts_client = base_session.client('sts')
    assume_role_response = sts_client.assume_role(RoleArn=role_arn, RoleSessionName=str(uuid.uuid4()))
    credentials = assume_role_response['Credentials']
    access_key = credentials['AccessKeyId']
    secret_key = credentials['SecretAccessKey']
    token = credentials['SessionToken']

    botocore_session = botocore.session.Session()
    botocore_session._credentials = botocore.credentials.Credentials(access_key,
                                                                     secret_key,
                                                                     token)
    return boto3.Session(botocore_session=botocore_session)
