import uuid
import botocore
from boto3 import Session
from .boto3_client_factory import client


def assume_role_session(role_arn: str, session: Session) -> Session:
    """
    Assume role
    :param role_arn: ARN to other role for assuming
    :param session: Base boto3 session
    :return: new assumed role
    """
    sts_client = client('sts', session)
    assume_role_response = sts_client.assume_role(RoleArn=role_arn, RoleSessionName=str(uuid.uuid4()))
    credentials = assume_role_response['Credentials']
    access_key = credentials['AccessKeyId']
    secret_key = credentials['SecretAccessKey']
    token = credentials['SessionToken']

    botocore_session = botocore.session.Session()
    botocore_session._credentials = botocore.credentials.Credentials(access_key,
                                                                     secret_key,
                                                                     token)
    return Session(botocore_session=botocore_session)
