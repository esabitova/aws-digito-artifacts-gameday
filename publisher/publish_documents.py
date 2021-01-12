import boto3
import getopt
import glob
import hashlib
import json
import logging
import os
import sys
import zipfile
from botocore.exceptions import ClientError

SCRIPT_DIR = '/documents/util/scripts/src'
SCRIPT_ZIP_FILE_NAME = 'digito_gameday_primitives.zip'
SCRIPT_BUCKET_NAME_PREFIX = 'digito-gameday-primitives'

logger = logging.getLogger('PublishDocuments')


class PublishDocuments:

    def __init__(self, region):
        self.root_dir = os.getcwd()
        self.ssm = boto3.client('ssm', region_name=region)
        self.s3 = boto3.resource('s3', region_name=region)
        self.sts = boto3.client('sts', region_name=region)
        self.region = region

    def publish_document(self, list_document_metadata):
        for document_metadata in list_document_metadata:
            doc_name = document_metadata['documentName']
            doc_type = document_metadata['documentType']
            doc_format = document_metadata['documentFormat']
            tag_value = document_metadata['tag']

            s3_attachment_url = None
            document_content = self.get_document_content(document_metadata)
            if 'attachments' in document_metadata:
                s3_attachment_url = 'https://s3.amazonaws.com/' + self.get_bucket_name() + '/' + SCRIPT_ZIP_FILE_NAME
            if self.document_exists(doc_name):
                if self.has_document_content_changed(doc_name, doc_format, document_content):
                    update_document_version = self.update_document(doc_name, document_content, doc_format,
                                                                   s3_attachment_url, tag_value)
                    self.update_document_default_version(doc_name, update_document_version)
                    logger.info('Updated document %s' % doc_name)
                else:
                    logger.info('Document content has not changed for document name, %s' % doc_name)
            else:
                self.create_document(doc_name, document_content, doc_type, doc_format, s3_attachment_url, tag_value)
                logger.info('Created document %s' % doc_name)

    def get_document_content(self, document_metadata):
        with open(document_metadata['location'] + '/' + document_metadata['documentContentPath'], 'r') as f:
            document_content = f.read()
            if 'attachments' in document_metadata:
                document_content = document_content + '\n' + self.get_files_attachment_snippet_in_document(
                    document_metadata['documentFormat'])
            return document_content

    def create_document(self, name, content, doc_type, doc_format, s3_attachment_url, tag_value):
        if s3_attachment_url is None:
            self.ssm.create_document(
                Content=content,
                Name=name,
                DocumentType=doc_type,
                DocumentFormat=doc_format,
                Tags=[
                    {
                        'Key': 'Digito-reference-id',
                        'Value': tag_value
                    },
                ]
            )
        else:
            self.ssm.create_document(
                Content=content,
                Attachments=[
                    {
                        'Key': 'S3FileUrl',
                        'Values': [
                            s3_attachment_url
                        ],
                        'Name': SCRIPT_ZIP_FILE_NAME
                    },
                ],
                Name=name,
                DocumentType=doc_type,
                DocumentFormat=doc_format,
                Tags=[
                    {
                        'Key': 'Digito-reference-id',
                        'Value': tag_value
                    },
                ]
            )

    def update_document(self, name, content, doc_format, s3_attachment_url, tag_value):
        update_document_response = {}
        try:
            if s3_attachment_url is None:
                update_document_response = self.ssm.update_document(
                    Content=content,
                    Name=name,
                    DocumentVersion='$LATEST',
                    DocumentFormat=doc_format
                )
            else:
                update_document_response = self.ssm.update_document(
                    Content=content,
                    Attachments=[
                        {
                            'Key': 'S3FileUrl',
                            'Values': [
                               s3_attachment_url
                            ],
                            'Name': SCRIPT_ZIP_FILE_NAME
                        },
                    ],
                    Name=name,
                    DocumentVersion='$LATEST',
                    DocumentFormat=doc_format
                )
                self.ssm.add_tags_to_resource(
                    ResourceType='Document',
                    ResourceId=name,
                    Tags=[
                        {
                            'Key': 'Digito-reference-id',
                            'Value': tag_value
                        },
                    ]
                )
                return update_document_response['DocumentDescription']['DocumentVersion']
        except ClientError as e:
            logger.error('Failed to update [{}] document.'.format(name))
        raise e

    def update_document_default_version(self, name, version):
        self.ssm.update_document_default_version(
            Name=name,
            DocumentVersion=version
        )

    def document_exists(self, name):
        try:
            self.ssm.describe_document(
                Name=name
            )
            return True
        except ClientError as e:
            return False

    def has_document_content_changed(self, name, doc_format, new_document_content):
        get_document_response = self.ssm.get_document(
            Name=name,
            DocumentVersion='$LATEST',
            DocumentFormat=doc_format
        )
        return new_document_content != get_document_response['Content']

    def read_metadata(self, file_path):
        try:
            with open(file_path) as metadata_file:
                document_metadata = json.load(metadata_file)
                return document_metadata
        except IOError as e:
            raise Exception('Could not open file %s', file_path, e)

    def file_exists(self, file_path):
        try:
            with open(file_path) as f:
                return True
        except IOError:
            return False

    def get_list_of_documents(self, file_name):
        list_document_metadata = []
        desired_documents_list = []
        # Include documents from file name
        with open(self.root_dir + '/' + file_name, "r") as f:
            desired_documents_list.extend(f.read().splitlines())

        files = glob.glob(self.root_dir + '/**/metadata.json', recursive=True)

        logger.info('Desired documents list %s' % desired_documents_list)
        # Find additional documents that are needed for desired documents
        for file in files:
            document_metadata = self.read_metadata(file)
            if 'dependsOn' in document_metadata and document_metadata['documentName'] in desired_documents_list:
                dependent_documents = document_metadata['dependsOn'].split(',')
                for dependent_document in dependent_documents:
                    if dependent_document not in desired_documents_list:
                        desired_documents_list.append(dependent_document)

        logger.info('Desired documents list including required documents : %s' % desired_documents_list)
        existing_document_names = []
        for file in files:
            document_metadata = self.read_metadata(file)
            existing_document_names.append(document_metadata['documentName'])
            if document_metadata['documentName'] in desired_documents_list:
                document_metadata['location'] = os.path.dirname(file)
                list_document_metadata.append(document_metadata)
            else:
                logger.debug('Not publishing %s' % document_metadata['documentName'])

        for desired_document_name in desired_documents_list:
            if desired_document_name not in existing_document_names:
                raise Exception("Document with name [{}] does not exist.".format(desired_document_name))

        return list_document_metadata

    def zip_scripts(self, script_relative_path):
        with zipfile.ZipFile(SCRIPT_ZIP_FILE_NAME, 'w', zipfile.ZIP_DEFLATED) as zipfile_handle:
            self.zip_dir(self.root_dir + script_relative_path, zipfile_handle)

    def zip_dir(self, path, zipfile_handle):
        for root, dirs, files in os.walk(path):
            os.chdir(root)
            for file in files:
                zipfile_handle.write(file)

        os.chdir(self.root_dir)

    def upload_scripts_to_s3(self):
        self.create_bucket_if_does_not_exist()
        self.zip_scripts(SCRIPT_DIR)
        self.upload_to_s3()

    def upload_to_s3(self):
        file_path = self.root_dir + '/' + SCRIPT_ZIP_FILE_NAME
        self.s3.meta.client.upload_file(file_path, self.get_bucket_name(), SCRIPT_ZIP_FILE_NAME)

    def create_bucket_if_does_not_exist(self):
        try:
            bucket_name = self.get_bucket_name()
            self.s3.meta.client.head_bucket(Bucket=bucket_name)
            logger.debug('Bucket %s Exists' % bucket_name)
        except ClientError:
            # The bucket does not exist or you have no access.
            logger.info('Bucket %s does not exist, creating' % bucket_name)
            # For us-east-1, s3 does not allow specifying location constraint
            if self.region == 'us-east-1':
                self.s3.create_bucket(Bucket=self.get_bucket_name())
            else:
                self.s3.create_bucket(
                    Bucket=self.get_bucket_name(),
                    CreateBucketConfiguration={'LocationConstraint': self.region})

    def get_bucket_name(self):
        # TODO https://issues.amazon.com/issues/Digito-671 support for custom bucket
        return '-'.join([SCRIPT_BUCKET_NAME_PREFIX, self.get_account_id(), self.region])

    def get_account_id(self):
        return self.sts.get_caller_identity()["Account"]

    def generate_file_checksum(self):
        with open(self.root_dir + '/' + SCRIPT_ZIP_FILE_NAME, "rb") as f:
            bytes = f.read() # read entire file as bytes
            readable_hash = hashlib.sha256(bytes).hexdigest()
            return readable_hash

    def get_file_size(self):
        return os.path.getsize(self.root_dir + '/' + SCRIPT_ZIP_FILE_NAME)

    def get_files_attachment_snippet_in_document(self, doc_format):
        if doc_format == 'YAML':
            with open(self.root_dir + '/publisher/FilesAttachmentSnippetYaml.yml', "r") as f:
                snippet = f.read() # read file
                snippet = snippet.replace('SHA256_PLACEHOLDER', self.generate_file_checksum())
                snippet = snippet.replace('SIZE_PLACEHOLDER', str(self.get_file_size()))
                return snippet
        else:
            logger.error('Unsupported format ' % doc_format)


def main(argv):
    region = 'us-west-2'
    log_level = logging.INFO
    file_name = 'manifest'
    try:
        opts, args = getopt.getopt(argv,"hr:l:f:", ["region=","log-level=","file-name="])
    except getopt.GetoptError:
        logger.info('usage: publish_document.py -r <region> -l <log-level> -f <file-name>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            logger.info('usage: publish_document.py -r <region> -l <log-level> -f <file-name>')
            sys.exit()
        elif opt in ("-r", "--region"):
            region = arg
        elif opt in ("-l", "--log-level"):
            log_level = arg
        elif opt in ("-f", "--file-name"):
            file_name = arg

    logging.basicConfig(
        format='%(asctime)s %(name)s %(levelname)s:%(message)s',
        level=log_level,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ])

    logger.info('Publishing documents in region %s' % region)

    p = PublishDocuments(region)

    # get list of documents from manifest file and their required documents
    list_document_metadata = p.get_list_of_documents(file_name)

    # upload python scripts to s3
    p.upload_scripts_to_s3()

    # publish documents to account
    p.publish_document(list_document_metadata)


if __name__ == "__main__":
    main(sys.argv[1:])

