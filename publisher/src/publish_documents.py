import boto3
import getopt
import glob
import json
import logging
import os
import sys
import publisher.src.document_metadata_attrs as metadata_attrs
from publisher.src.document_validator import DocumentValidator
from botocore.config import Config
from botocore.exceptions import ClientError

SCRIPT_DIR = '/documents/util/scripts/src'
default_logger = logging.getLogger('PublishDocuments')


class PublishDocuments:

    def __init__(self, boto3_session, logger=None):
        self.root_dir = os.getcwd()
        config = Config(retries={'max_attempts': 20, 'mode': 'standard'})
        self.ssm = boto3_session.client('ssm', config=config)
        self.document_validator = DocumentValidator()
        self.logger = logger if logger else default_logger

    def publish_document(self, list_document_metadata):
        for document_metadata in list_document_metadata:
            doc_name = document_metadata['documentName']
            doc_type = document_metadata['documentType']
            doc_format = document_metadata['documentFormat']
            tag_value = document_metadata['tag']

            self.validate_metadata(document_metadata)
            document_content = self.get_document_content(document_metadata)
            try:
                if self.document_exists(doc_name):
                    if self.has_document_content_changed(doc_name, doc_format, document_content):
                        self.update_document(doc_name, document_content, doc_format, tag_value)
                        self.logger.info('Updated document %s' % doc_name)
                    else:
                        self.logger.info('Document content has not changed for document name, %s' % doc_name)
                else:
                    self.create_document(doc_name, document_content, doc_type, doc_format, tag_value)
                    self.logger.info('Created document %s' % doc_name)
            except ClientError as error:
                self.logger.error('Failed to publish [{}] document.'.format(doc_name))
                raise error

    def get_document_content(self, document_metadata):
        updated_document_content = ""
        with open(document_metadata['location'] + '/' + document_metadata['documentContentPath'], 'r') as f:
            document_content_lines = f.read().splitlines()
            for line in document_content_lines:
                if ("SCRIPT_PLACEHOLDER" in line):
                    script_placeholder = line.strip()
                    line = self.replace_script_placeholder_in_document_content(line, script_placeholder)
                updated_document_content += line + "\n"
        return updated_document_content

    def create_document(self, name, content, doc_type, doc_format, tag_value):
        try:
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
        except ClientError as error:
            if error.response['Error']['Code'] == 'DocumentAlreadyExists':
                self.logger.warning(error.response['Error']['Message'])
            else:
                self.logger.error('Failed to create [{}] document.'.format(name))
                raise error

    def update_document(self, name, content, doc_format, tag_value):
        try:
            update_document_response = self.ssm.update_document(
                Content=content,
                Name=name,
                DocumentVersion='$LATEST',
                DocumentFormat=doc_format
            )
            document_version = update_document_response['DocumentDescription']['DocumentVersion']
            self.update_document_default_version(name, document_version)
        except ClientError as error:
            if error.response['Error']['Code'] == 'DuplicateDocumentContent':
                self.logger.warning(error.response['Error']['Message'])
            else:
                self.logger.error('Failed to update [{}] document.'.format(name))
                raise error

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
        except ClientError:
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

    def get_documents_list_by_manifest_file(self, manifest_file_name):
        desired_documents_list = []
        # Include documents from file name
        with open(self.root_dir + '/' + manifest_file_name, "r") as f:
            desired_documents_list.extend(f.read().splitlines())
        return self.get_documents_list_by_names(desired_documents_list)

    def get_documents_list_by_names(self, desired_documents_list: []):
        list_document_metadata = []
        files = glob.glob(self.root_dir + '/documents/**/metadata.json', recursive=True)

        self.logger.info('Desired documents list %s' % desired_documents_list)
        # Find additional documents that are needed for desired documents
        for file in files:
            document_metadata = self.read_metadata(file)
            if 'dependsOn' in document_metadata and document_metadata['documentName'] in desired_documents_list:
                dependent_documents = document_metadata['dependsOn'].split(',')
                for dependent_document in dependent_documents:
                    if dependent_document not in desired_documents_list:
                        desired_documents_list.append(dependent_document)

        self.logger.info('Desired documents list including required documents : %s' % desired_documents_list)
        existing_document_names = []
        for file in files:
            # Skipping alarms (alarms are not SSM automation documents):
            # https://issues.amazon.com/issues/Digito-1743
            if '/alarm/' not in str(file):
                document_metadata = self.read_metadata(file)
                existing_document_names.append(document_metadata['documentName'])
                if document_metadata['documentName'] in desired_documents_list:
                    document_metadata['location'] = os.path.dirname(file)
                    list_document_metadata.append(document_metadata)
                else:
                    self.logger.debug('Not publishing %s' % document_metadata['documentName'])

        for desired_document_name in desired_documents_list:
            if desired_document_name not in existing_document_names:
                raise Exception("Document with name [{}] does not exist.".format(desired_document_name))

        return list_document_metadata

    def replace_script_placeholder_in_document_content(self, document_content, script_placeholder):
        script_content = self.get_script(script_placeholder)
        document_content = document_content.replace(script_placeholder, script_content)
        return document_content

    def get_script(self, script_placeholder):
        script_file_name = script_placeholder.split("::")[1].split(".")[0]
        script_method_name = script_placeholder.split("::")[1].split(".")[1]

        script_lines = []
        script_lines_to_be_included = ""
        with open(self.root_dir + '/documents/util/scripts/src/' + script_file_name + '.py') as f:
            script_lines = f.read().splitlines()

        is_first = True
        before_first_method = True
        found_method = False

        for line in script_lines:
            if (before_first_method and "def " in line):
                before_first_method = False

            # method ended, found another method, return
            if (found_method and ("def " in line)):
                return script_lines_to_be_included

            if ("def " + script_method_name + "(" in line):
                found_method = True

            if ((before_first_method and script_method_name == "imports") or found_method):
                # Add 8 spaces to all lines except first line so that it aligns with ssm document yaml format
                if (is_first):
                    is_first = False
                else:
                    line = "        " + line
                script_lines_to_be_included += line + "\n"

        return script_lines_to_be_included

    def validate_metadata(self, document_metadata):
        """
        Validates metadata.json files for SSM documents based on given required attributes
        and returns failed attributes messages for given metadata.json file.
        :param document_metadata The metadata.json file content
        """
        metadata_file_path = document_metadata['location'] + '/metadata.json'
        meta_attrs_map = metadata_attrs.metadata_attrs_map
        required_attributes = []
        if '/test/' in metadata_file_path:
            required_attributes = meta_attrs_map.get('test')
        elif '/sop/' in metadata_file_path:
            required_attributes = meta_attrs_map.get('sop')
        violations = self.get_metadata_violations(document_metadata, metadata_file_path, required_attributes)

        for violation in violations:
            logging.error(violation)
        if len(violations) > 0:
            raise Exception("Detected [{}] metadata.json structural violations. Check ERROR logs for more details."
                            .format(len(violations)))

    def get_metadata_violations(self, document_metadata, metadata_file_path, required_attributes):
        """
        Validates metadata.json files for SSM documents based on given required attributes
        and returns failed attributes messages for given metadata.json file.
        :param required_attributes The list of required attributes should be presented in metadata file.
        :param document_metadata The metadata.json file content
        :param metadata_file_path The metadata.json file path.
        """
        failed_fields = []
        for rf in required_attributes:
            value = document_metadata.get(rf)
            if not value:
                failed_fields.append('Required attribute [{}] missing in [{}].'.format(rf, metadata_file_path))
            if rf in metadata_attrs.metadata_valid_values_map:
                if rf == 'failureType':
                    failure_types = value.split(",")
                    for failure_type in failure_types:
                        if failure_type not in metadata_attrs.metadata_valid_values_map.get(rf):
                            failed_fields.append('Invalid value [{}] for attribute [{}] in [{}].'
                                                 .format(failure_type, rf, metadata_file_path))
                else:
                    if value not in metadata_attrs.metadata_valid_values_map.get(rf):
                        failed_fields.append('Invalid value [{}] for attribute [{}] in [{}].'
                                             .format(value, rf, metadata_file_path))

        #tag = document_metadata.get('tag').split(":")  # Tag as an array [compute,test,asg-inject_cpu_load,2020-07-08]
        # path as an array [documents, compute, test, asg-inject_cpu_load, 2020-07-08, Documents, metadata.json]
        #parsed_path = os.path.normpath(metadata_file_path).split(os.sep)
        #if tag != parsed_path[1:-2]:
        #    failed_fields.append(f'Invalid tag {":".join(tag)} for document at path {os.sep.join(parsed_path[1:-2])}')
        return failed_fields


def main(argv):
    region = 'us-west-2'
    log_level = logging.INFO
    file_name = 'manifest'
    try:
        opts, args = getopt.getopt(argv, "hr:l:f:", ["region=", "log-level=", "file-name="])
    except getopt.GetoptError:
        default_logger.info('usage: publish_document.py -r <region> -l <log-level> -f <file-name>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            default_logger.info('usage: publish_document.py -r <region> -l <log-level> -f <file-name>')
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

    default_logger.info('Publishing documents in region %s' % region)
    p = PublishDocuments(boto3.Session(region_name=region))

    # get list of documents from manifest file and their required documents
    list_document_metadata = p.get_documents_list_by_manifest_file(file_name)

    # publish documents to account
    p.publish_document(list_document_metadata)


if __name__ == "__main__":
    main(sys.argv[1:])
