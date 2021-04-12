import logging
from botocore.exceptions import ClientError
from cfn_tools import dump_yaml
from .util.boto3_client_factory import client, resource


class S3:
    """
    Class to manipulate with S3 ResourceManager created buckets/files.
    """
    def __init__(self, boto3_session):
        self.session = boto3_session
        self.client = client('s3', boto3_session)
        self.resource = resource('s3', boto3_session)

    def upload_file(self, file_name: str, content: dict):
        """
        Uploads Cloud Formation template file to S3 to be used for template stack deployment.
        :return: True if uploaded, False otherwise
        """
        bucket_name = self.get_bucket_name()
        try:
            if not self.bucket_exists(bucket_name):
                self._create_bucket(bucket_name)
            # In case if template already exist it is possible that we want to update it.
            logging.info('Uploading CF template [%s] to S3 bucket [%s]', file_name, bucket_name)
            self._put_object_as_yaml(bucket_name, file_name, content)
            return self._get_file_url(file_name)
        except ClientError as e:
            logging.error('Failed to upload CF template [%s] to S3 bucket [%s]:\n %s', file_name,
                          bucket_name, e.response)
            raise e

    def _create_bucket(self, bucket_name):
        """
        Creates S3 bucket based on region, for 'us-east-1' region 'LocationConstraint' is not given:\n
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.create_bucket
        :param bucket_name: The S3 bucket name
        """
        region_name = self.session.region_name
        try:
            if region_name == 'us-east-1':
                self.client.create_bucket(Bucket=bucket_name)
            else:
                config = {'LocationConstraint': region_name}
                self.client.create_bucket(Bucket=bucket_name, CreateBucketConfiguration=config)
        except ClientError as e:
            if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
                logging.warning("Bucket with name [{}] for region [{}] already exist.".format(bucket_name, region_name))
            else:
                raise e

    def _get_file_url(self, file_name):
        """
        Returns cloud formation template URL located in S3 bucket.
        :return: The cloud formation template URL
        """
        # TODO(semiond): Secure bucket by appending UUID, so that attacker will not be able to guess name:
        # https://issues.amazon.com/issues/Digito-1287
        region_name = self.session.region_name
        bucket_name = self.get_bucket_name()
        if region_name == 'us-east-1':
            return 'https://{}.s3.amazonaws.com/{}'.format(bucket_name, file_name)
        else:
            return 'https://{}.s3.{}.amazonaws.com/{}'.format(bucket_name, region_name, file_name)

    def _get_account_id(self):
        sts_client = self.session.client('sts')
        caller_id = sts_client.get_caller_identity()
        return caller_id.get('Account')

    def get_bucket_name(self):
        """
        Returns S3 bucket name.
        :return: The S3 bucket name
        """
        account_id = self._get_account_id()
        region_name = self.session.region_name
        return 'ssm-test-resources-{}-{}'.format(account_id, region_name)

    def delete_bucket(self, bucket_name):
        """
        Deletes S3 bucket which is associated with this class instance.
        :param bucket_name The bucket name to be deleted.
        """
        try:
            if self.bucket_exists(bucket_name):
                logging.info('Deleting CF bucket with name [%s]', bucket_name)
                for key in self._get_bucket_keys(bucket_name):
                    self.client.delete_objects(
                        Bucket=bucket_name,
                        Delete={'Objects': [{'Key': key}]}
                    )
                self.client.delete_bucket(Bucket=bucket_name)
        except ClientError as e:
            logging.error('Failed to delete S3 bucket with name [%s]', bucket_name, e)
            raise e

    def _get_bucket_keys(self, bucket_name):
        """
        Returns all S3 bucket keys for given bucket name.
        :return: The S3 bucket keys
        """
        bucket = self.resource.Bucket(bucket_name)
        obj_keys = []
        for obj in bucket.objects.all():
            obj_keys.append(obj.key)
        return obj_keys

    def bucket_key_exist(self, bucket_name, key):
        """
        True is S3 bucekt key exist for given bucket name and key.
        :param bucket_name The S3 bucket name
        :param key: The S3 bucket key
        :return: True is exist, False otherwise
        """
        return key in self._get_bucket_keys(bucket_name)

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
        '''
        Returns S3 file content by given bucket and file name.
        :param bucket_name The S3 bucket name
        :param file_name The S3 file name
        '''
        try:
            s3_object = self.resource.Object(bucket_name, file_name)
            return s3_object.get()['Body'].read().decode('utf-8')
        except ClientError as e:
            if e.response['Error']['Code'] == "404" or e.response['Error']['Code'] == 'NoSuchKey':
                return None
            else:
                raise e

    def _put_object_as_yaml(self, bucket_name: str, file_name: str, content: dict):
        '''
        Uploads yamml file to S3.
        :param bucket_name The S3 bucket name
        :param file_name The name of the file to uploaded
        :param content The content of the file to be uploaded
        '''
        s3_object = self.resource.Object(bucket_name, file_name)
        s3_object.put(Body=(bytes(dump_yaml(content).encode('UTF-8'))))
