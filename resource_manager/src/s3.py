import logging
import os

from botocore.exceptions import ClientError
from cfn_tools import dump_yaml

from .constants import s3_bucket_name_pattern
from .util.boto3_client_factory import client, resource


class S3:
    """
    Class to manipulate with S3 ResourcePool created buckets/files.
    """

    def __init__(self, boto3_session, aws_account_id, logger=logging.getLogger()):
        self.session = boto3_session
        self.aws_account_id = aws_account_id
        self.client = client('s3', boto3_session)
        self.resource = resource('s3', boto3_session)
        self.logger = logger

    def upload_file(self, file_name: str, content: dict):
        """
        Uploads Cloud Formation template file to S3 to be used for template stack deployment.
        :return: True if uploaded, False otherwise
        """
        bucket_name = self.get_bucket_name()
        try:
            self._create_bucket_if_not_exist(bucket_name)
            # In case if template already exist it is possible that we want to update it.
            self.logger.info('Uploading CF template [%s] to S3 bucket [%s]', file_name, bucket_name)
            self._put_object_as_yaml(bucket_name, file_name, content)
            return self._get_file_url(bucket_name, file_name)
        except ClientError as e:
            self.logger.error('Failed to upload CF template [%s] to S3 bucket [%s]:\n %s', file_name,
                              bucket_name, e.response)
            raise e

    def upload_local_file(self, object_key: str, file_relative_path: str, bucket_name: str = None, metadata: dict = {}):
        """
        Uploads file to S3 from the local disk
        :param bucket_name: the bucket name where the file will be uploaded. If it's empty then default s3 bucket
        is used
        :param object_key: the name of future S3 object
        :param file_relative_path: relative path to the file from the project's absolute path
        :param metadata: dict of metadata to set for file
        :return: Url, bucket name, object key, version id
        """
        if not bucket_name:
            bucket_name = self.get_bucket_name()
        try:
            self._create_bucket_if_not_exist(bucket_name)
            # In case if template already exist it is possible that we want to update it.
            file_abs_path = os.getcwd() + ("/" if not file_relative_path.startswith("/") else "") + file_relative_path
            logging.info(f'Uploading file [{file_abs_path}] to S3 bucket [{bucket_name}]\n metadata: {metadata}')
            upload_response = self._upload_local_file(bucket_name, object_key, file_abs_path, metadata)
            version_id = upload_response['VersionId'] if 'VersionId' in upload_response else ''
            url = self._get_file_url(bucket_name, object_key)
            logging.info(f'File uploaded: url = {url}, bucket_name = {bucket_name}, object_key = {object_key}, '
                         f'version_id = {version_id}, metadata: {metadata}')
            return url, bucket_name, object_key, version_id
        except ClientError as e:
            logging.error('Failed to upload file [%s] to S3 bucket [%s]:\n %s', object_key,
                          bucket_name, e.response)
            raise e

    def _create_bucket_if_not_exist(self, bucket_name):
        """
        Create bucket if not exist
        :param bucket_name: bucket to create
        :return:  None
        """
        if not self.bucket_exists(bucket_name):
            self._create_bucket(bucket_name)

    def _create_bucket(self, bucket_name):
        """
        Creates S3 bucket based on region, for 'us-east-1' region 'LocationConstraint' is not given:\n
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.create_bucket
        :param bucket_name: The S3 bucket name
        """
        region_name = self.session.region_name
        try:
            if region_name == 'us-east-1':
                self.client.create_bucket(ACL='private', Bucket=bucket_name)
            else:
                self.client.create_bucket(ACL='private', Bucket=bucket_name, CreateBucketConfiguration={
                    'LocationConstraint': region_name
                })

        except ClientError as e:
            if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
                self.logger.warning(f"Bucket with name [{bucket_name}] for region [{region_name}] already exist.")
            else:
                raise e

        self.client.put_bucket_versioning(Bucket=bucket_name, VersioningConfiguration={'Status': 'Enabled'})

    def _get_file_url(self, bucket_name, key):
        """
        Returns file URL located in S3 bucket.
        :return: The file URL
        """
        return self.client.generate_presigned_url('get_object', Params={
            'Bucket': bucket_name,
            'Key': key
        }, ExpiresIn=3600)

    def get_bucket_name(self):
        """
        Returns S3 bucket name.
        :return: The S3 bucket name
        """
        account_id = self.aws_account_id
        region_name = self.session.region_name
        return s3_bucket_name_pattern.replace('<account_id>', account_id).replace('<region_name>', region_name)

    def delete_bucket(self, bucket_name):
        """
        Deletes S3 bucket which is associated with this class instance.
        :param bucket_name The bucket name to be deleted.
        """
        try:
            if self.bucket_exists(bucket_name):
                self.logger.info('Deleting CF bucket with name [%s]', bucket_name)
                bucket = self.resource.Bucket(bucket_name)
                if self.resource.BucketVersioning(bucket_name).status == 'Enabled':
                    bucket.object_versions.delete(ExpectedBucketOwner=self.aws_account_id)
                else:
                    bucket.objects.delete(ExpectedBucketOwner=self.aws_account_id)
                self.client.delete_bucket(Bucket=bucket_name, ExpectedBucketOwner=self.aws_account_id)
        except ClientError as e:
            self.logger.error('Failed to delete S3 bucket with name [%s]', bucket_name, e)
            raise e

    def bucket_key_exist(self, bucket_name, key):
        """
        True is S3 bucket key exist for given bucket name and key.
        :param bucket_name The S3 bucket name
        :param key: The S3 bucket key
        :return: True is exist, False otherwise
        """
        try:
            self.client.head_object(Bucket=bucket_name,
                                    Key=key,
                                    ExpectedBucketOwner=self.aws_account_id)
            return True
        except ClientError:
            return False

    def bucket_exists(self, bucket_name):
        """
        Checks if S3 bucket exists.
        :return: True is exists, False otherwise
        """
        for bucket in self.resource.buckets.all():
            if bucket_name == bucket.name:
                return True
        return False

    def get_file_content(self, bucket_name, file_name):
        """
        Returns S3 file content by given bucket and file name.
        :param bucket_name The S3 bucket name
        :param file_name The S3 file name
        """
        try:
            s3_object = self.resource.Object(bucket_name, file_name)
            return s3_object.get(ExpectedBucketOwner=self.aws_account_id)['Body'].read().decode('utf-8')
        except ClientError as e:
            if e.response['Error']['Code'] == "404" or e.response['Error']['Code'] == 'NoSuchKey':
                return None
            else:
                raise e

    def _put_object_as_yaml(self, bucket_name: str, file_name: str, content: dict):
        """
        Uploads yaml file to S3.
        :param bucket_name The S3 bucket name
        :param file_name The name of the file to uploaded
        :param content The content of the file to be uploaded
        """
        s3_object = self.resource.Object(bucket_name, file_name)
        s3_object.put(ExpectedBucketOwner=self.aws_account_id, Body=(bytes(dump_yaml(content).encode('UTF-8'))))

    def _upload_local_file(self, bucket_name: str, object_key: str, file_abs_path: str, metadata: dict = {}) -> dict:
        """
        Upload the file from local disk
        :param bucket_name: S3 bucket where the file will be uploaded
        :param object_key: S3 key where the file will be uploaded
        :param file_abs_path: Absolute path to the file
        :return Response from put_object method
        """
        with open(file_abs_path, 'rb') as file:
            return self.client.put_object(
                Bucket=bucket_name,
                Key=object_key,
                Body=file,
                Metadata=metadata
            )

    def retrieve_object_metadata(self, bucket_name: str, object_key: str) -> dict:
        """
        Retrieves and returns object metadata
        :param bucket_name: S3 bucket where the file will be uploaded
        :param object_key: S3 key where the file will be uploaded
        :return: Response from head_object method
        """
        try:
            response = self.client.head_object(
                Bucket=bucket_name,
                Key=object_key,
            )
            uri = self._get_file_url(bucket_name, object_key)
            return {
                "Object": response,
                "Uri": uri
            }
        except ClientError as err:
            if err.response['Error']['Code'] == "404" or err.response['Error']['Code'] == 'NoSuchKey':
                return {}
            else:
                raise err
