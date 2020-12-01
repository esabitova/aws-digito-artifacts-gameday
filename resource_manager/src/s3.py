import logging
import boto3
import botocore
from botocore.exceptions import ClientError


class S3:
    """
    Class to manipulate with S3 ResourceManager created buckets/files.
    """

    @staticmethod
    def upload_file(file_name):

        """
        Uploads Cloud Formation template file to S3 to be used for template stack deployment.
        :return: True if uploaded, False otherwise
        """
        try:
            bucket_name = S3.get_bucket_name()
            if not S3.bucket_exists(bucket_name):
                S3._create_bucket(bucket_name)
            # In case if template already exist it is possible that we want to update it.
            logging.info('Uploading CF template [%s] to S3 bucket [%s]', file_name, bucket_name)
            S3._get_client().upload_file(file_name, bucket_name, file_name)
            return S3._get_file_url(file_name)
        except Exception as e:
            logging.error('Failed to upload CF template [%s] to S3 bucket [%s]', file_name, bucket_name)
            raise e

    @staticmethod
    def _create_bucket(bucket_name):
        """
        Creates S3 bucket based on region, for 'us-east-1' region 'LocationConstraint' is not given:\n
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.create_bucket
        :param bucket_name: The S3 bucket name
        """
        if S3._get_region() == 'us-east-1':
            S3._get_client().create_bucket(Bucket=bucket_name)
        else:
            config = {'LocationConstraint': S3._get_region()}
            S3._get_client().create_bucket(Bucket=bucket_name, CreateBucketConfiguration=config)

    @staticmethod
    def _get_file_url(file_name):
        """
        Returns cloud formation template URL located in S3 bucket.
        :return: The cloud formation template URL
        """
        # TODO(semiond): Secure bucket by appending UUID, so that attcker will not be able to guess name:
        # https://issues.amazon.com/issues/Digito-1287
        return 'https://{}.s3-{}.amazonaws.com/{}'.format(S3.get_bucket_name(), S3._get_region(), file_name)

    @staticmethod
    def _get_region():
        session = boto3.session.Session()
        return session.region_name

    @staticmethod
    def _get_client():
        return boto3.client('s3')

    @staticmethod
    def _get_resource():
        return boto3.resource('s3')

    @staticmethod
    def _get_account_id():
        sts_client = boto3.client('sts')
        caller_id = sts_client.get_caller_identity()
        return caller_id.get('Account')

    @staticmethod
    def get_bucket_name():
        """
        Returns S3 bucket name.
        :return: The S3 bucket name
        """
        return 'ssm-test-resources-{}-{}'.format(S3._get_account_id(), S3._get_region())

    @staticmethod
    def delete_bucket(bucket_name):
        """
        Deletes S3 bucket which is associated with this class instance.
        """
        try:
            if S3.bucket_exists(bucket_name):
                logging.info('Deleting CF bucket with name [%s]', bucket_name)
                for key in S3.get_bucket_keys(bucket_name):
                    S3._get_client().delete_objects(
                        Bucket=bucket_name,
                        Delete={'Objects': [{'Key': key}]}
                    )
                S3._get_client().delete_bucket(Bucket=bucket_name)
        except ClientError as e:
            logging.error('Failed to delete S3 bucket with name [%s]', bucket_name, e)
            raise e

    @staticmethod
    def get_bucket_keys(bucket_name):
        """
        Returns all S3 bucket keys for given bucket name.
        :return: The S3 bucket keys
        """
        bucket = S3._get_resource().Bucket(bucket_name)
        obj_keys = []
        for obj in bucket.objects.all():
            obj_keys.append(obj.key)
        return obj_keys

    @staticmethod
    def bucket_key_exist(bucket_name, key):
        """
        True is S3 bucekt key exist for given bucket name and key.
        :param key: The S3 bucket key
        :return: True is exist, False otherwise
        """
        return key in S3.get_bucket_keys(bucket_name)

    @staticmethod
    def bucket_exists(bucket_name):
        """
        Checks if S3 bucket exists.
        :return: True is exists, False otherwise
        """
        for bucket in S3._get_resource().buckets.all():
            if bucket_name == bucket.name:
                return True
        return False
