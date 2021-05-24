import botocore
import boto3


class RoleSession(boto3.session.Session):
    """
    Boto3 session that assumes a role via temporary session and refreshes as needed.
    With IAM role credentials will be refreshed every time boto3 client is created as
    well as if client session is exceeding 1 hour (to avoid session expiration).
    However we need to make sure that credentials (credential_session) which are used to assume this role
    will not exceed session time limit as well.
    """

    def refresh_external_credentials(self):
        client = self.credential_session.client('sts')
        response = client.assume_role(
            RoleArn=self.iam_role_arn,
            RoleSessionName=self.session_name,
            DurationSeconds=self.duration
        )
        return {
            "access_key": response['Credentials']['AccessKeyId'],
            "secret_key": response['Credentials']['SecretAccessKey'],
            "token": response['Credentials']['SessionToken'],
            "expiry_time": response['Credentials']['Expiration'].isoformat()
        }

    def __init__(self, iam_role_arn: str, session_name: str, credential_session: boto3.session.Session,
                 duration: int = 900):
        self.iam_role_arn = iam_role_arn
        self.session_name = session_name
        self.duration = duration
        self.credential_session = credential_session

        refreshing_session = botocore.session.Session(profile=credential_session.profile_name)
        refreshing_session._credentials = botocore.credentials.RefreshableCredentials.create_from_metadata(
            metadata=self.refresh_external_credentials(),
            refresh_using=self.refresh_external_credentials,
            method='sts-assume-role'
        )
        boto3.session.Session.__init__(self, botocore_session=refreshing_session)
