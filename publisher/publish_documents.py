import boto3
import botocore
from botocore.exceptions import ClientError
import getopt
import glob
import hashlib
import json
import logging
import os
import sys
import zipfile

SCRIPT_DIR = '/documents/util/scripts/src'
SCRIPT_ZIP_FILE_NAME = 'digito_gameday_primitives.zip'
SCRIPT_BUCKET_NAME_PREFIX = 'digito-gameday-primitives'

logger = logging.getLogger('PublishDocuments')

class PublishDocuments:
    def __init__(self, region):
        self.rootdir = os.getcwd()
        self.ssm = boto3.client('ssm', region_name=region)
        self.s3 = boto3.resource('s3', region_name=region)
        self.sts = boto3.client('sts', region_name=region)
        self.region = region

    def publish_document(self, list_document_metadata):
        for document_metadata in list_document_metadata:
            name = document_metadata['documentName']
            type = document_metadata['documentType']
            format = document_metadata['documentFormat']
            tag_value = document_metadata['tag']
            s3AttachmentUrl = None
            document_content = self.get_document_content(document_metadata)
            if ('attachments' in document_metadata):
                s3AttachmentUrl = 'https://s3.amazonaws.com/' + self.get_bucket_name() + '/' + SCRIPT_ZIP_FILE_NAME
            if (self.document_exists(name)):
                if (self.has_document_content_changed(name, format, document_content)):
                    update_document_version = self.update_document(name, document_content, format, s3AttachmentUrl, tag_value)
                    self.update_document_default_version(name, update_document_version)
                    logger.info('Updated document %s' % name)
                else:
                    logger.info('Document content has not changed for document name, %s' % name)
            else:
                self.create_document(name, document_content, type, format, s3AttachmentUrl, tag_value)
                logger.info('Created document %s' % name)

    def get_document_content(self, document_metadata):
        with open(document_metadata['location'] + '/' + document_metadata['documentContentPath'], 'r') as f:
            document_content = f.read()
            if ('attachments' in document_metadata):
                document_content = document_content + '\n' + self.getFilesAttachmentSnippetInDocument(document_metadata['documentFormat'])

            return document_content

    def create_document(self, name, content, type, format, s3AttachmentUrl, tag_value):
        if (s3AttachmentUrl == None):
            self.ssm.create_document(
                Content = content,
                Name = name,
                DocumentType = type,
                DocumentFormat = format,
                Tags=[
                    {
                        'Key': 'Digito-reference-id',
                        'Value': tag_value
                    },
                ]
            )
        else:
            self.ssm.create_document(
                Content = content,
                Attachments = [
                    {
                        'Key': 'S3FileUrl',
                        'Values': [
                            s3AttachmentUrl
                        ],
                        'Name': SCRIPT_ZIP_FILE_NAME
                    },
                ],
                Name = name,
                DocumentType = type,
                DocumentFormat = format,
                Tags=[
                    {
                        'Key': 'Digito-reference-id',
                        'Value': tag_value
                    },
                ]
            )

    def update_document(self, name, content, format, s3AttachmentUrl, tagValue):
        update_document_response = {}

        if (s3AttachmentUrl == None):
            update_document_response = self.ssm.update_document(
                Content = content,
                Name = name,
                DocumentVersion = '$LATEST',
                DocumentFormat = format
            )
        else:
            update_document_response = self.ssm.update_document(
                Content = content,
                Attachments = [
                    {
                        'Key': 'S3FileUrl',
                        'Values': [
                            s3AttachmentUrl
                        ],
                        'Name': SCRIPT_ZIP_FILE_NAME
                    },
                ],
                Name = name,
                DocumentVersion = '$LATEST',
                DocumentFormat = format
            )

        self.ssm.add_tags_to_resource(
            ResourceType='Document',
            ResourceId=name,
            Tags=[
                {
                    'Key': 'Digito-reference-id',
                    'Value': tagValue
                },
            ]
        )
        return update_document_response['DocumentDescription']['DocumentVersion']

    def update_document_default_version(self, name, version):
        self.ssm.update_document_default_version(
            Name = name,
            DocumentVersion = version
        )

    def document_exists(self, name):
        try:
            self.ssm.describe_document(
                Name = name
            )
            return True
        except ClientError as e:
            return False

    def has_document_content_changed(self, name, format, new_document_content):
        get_document_response = self.ssm.get_document(
            Name = name,
            DocumentVersion = '$LATEST',
            DocumentFormat = format
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
        desiredDocumentsList = []
        # Include documents from file name
        with open(self.rootdir + '/' + file_name,"r") as f:
            desiredDocumentsList.extend(f.read().splitlines())

        files = glob.glob(self.rootdir + '/**/metadata.json', recursive=True)

        logger.info('Desired documents list %s' % desiredDocumentsList)
        # Find additional documents that are needed for desired documents
        for file in files:
            document_metadata = self.read_metadata(file)
            if ('dependsOn' in document_metadata and document_metadata['documentName'] in desiredDocumentsList):
                dependent_documents = document_metadata['dependsOn'].split(',')
                for dependent_document in dependent_documents:
                    if (dependent_document not in desiredDocumentsList):
                        desiredDocumentsList.append(dependent_document)

        logger.info('Desired documents list including required documents : %s' % desiredDocumentsList)
        for file in files:
            document_metadata = self.read_metadata(file)
            if (document_metadata['documentName'] in desiredDocumentsList):
                document_metadata['location'] = os.path.dirname(file)
                list_document_metadata.append(document_metadata)
            else:
                logger.debug('Not publishing %s' % document_metadata['documentName'])

        if (len(desiredDocumentsList) != len(list_document_metadata)):
            logger.info('Desired documents list %s' % desiredDocumentsList)
            logger.info('Found documents metadata list %s' % list_document_metadata)
            raise Exception('Expected same number of documents')

        return list_document_metadata

    def zipScripts(self, script_relative_path):
        with zipfile.ZipFile(SCRIPT_ZIP_FILE_NAME, 'w', zipfile.ZIP_DEFLATED) as zipfile_handle:
            self.zipdir(self.rootdir + script_relative_path, zipfile_handle)

    def zipdir(self, path, zipfile_handle):
        for root, dirs, files in os.walk(path):
            os.chdir(root)
            for file in files:
                zipfile_handle.write(file)

        os.chdir(self.rootdir)

    def upload_scripts_to_s3(self):
        self.create_bucket_if_does_not_exist()
        self.zipScripts(SCRIPT_DIR)
        self.uploadToS3()

    def uploadToS3(self):
        self.s3.meta.client.upload_file(self.rootdir + '/' + SCRIPT_ZIP_FILE_NAME, self.get_bucket_name(), SCRIPT_ZIP_FILE_NAME)

    def create_bucket_if_does_not_exist(self):
        try:
            bucket_name = self.get_bucket_name()
            self.s3.meta.client.head_bucket(Bucket=bucket_name)
            logger.debug('Bucket %s Exists' % bucket_name)
        except ClientError:
            # The bucket does not exist or you have no access.
            logger.info('Bucket %s does not exist, creating' % bucket_name)
            # For us-east-1, s3 does not allow specifying location constraint
            if (self.region == 'us-east-1'):
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

    def generateFileChecksum(self):
        with open(self.rootdir + '/' + SCRIPT_ZIP_FILE_NAME,"rb") as f:
            bytes = f.read() # read entire file as bytes
            readable_hash = hashlib.sha256(bytes).hexdigest()
            return readable_hash

    def getFileSize(self):
        return os.path.getsize(self.rootdir + '/' + SCRIPT_ZIP_FILE_NAME)

    def getFilesAttachmentSnippetInDocument(self, format):
        if (format == 'YAML'):
            with open(self.rootdir + '/publisher/FilesAttachmentSnippetYaml.yml',"r") as f:
                snippet = f.read() # read file
                snippet = snippet.replace('SHA256_PLACEHOLDER', self.generateFileChecksum())
                snippet = snippet.replace('SIZE_PLACEHOLDER', str(self.getFileSize()))
                return snippet
        else:
            logger.error('Unsupported format ' % format)

def main(argv):
    region = 'us-west-2'
    log_level = logging.INFO
    file_name = 'manifest'
    try:
        opts, args = getopt.getopt(argv,"hr:l:f:",["region=","log-level=","file-name="])
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

