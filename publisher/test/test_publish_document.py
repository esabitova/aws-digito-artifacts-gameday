import json
import logging
import os
import unittest

import boto3
import pytest
import yaml

import publisher.src.document_metadata_attrs as metadata_attrs
from publisher.src.document_validator import DocumentValidator
from publisher.src.global_metadata_validator import GlobalMetadataValidator
from publisher.src.publish_documents import PublishDocuments


class TestPublishDocuments(unittest.TestCase):
    target_service = ""

    @pytest.fixture(autouse=True)
    def __get_service_fixture(self, target_service):
        self.target_service = target_service

    @pytest.mark.style_validator
    @pytest.mark.metadata_validator
    def test_validate_metadata_files(self):
        pd = PublishDocuments(boto3.Session())
        meta_attrs_map = metadata_attrs.metadata_attrs_map
        fail_messages = []
        global_metadata_validator = GlobalMetadataValidator()
        for root, dirs, files in os.walk("documents"):
            if "not_completed" in dirs:
                dirs.remove('not_completed')
            if "util" in dirs:
                dirs.remove('util')

            for f in files:
                if f == 'metadata.json':
                    file_path = os.path.join(root, f)
                    with open(file_path) as metadata_file:
                        document_metadata = json.load(metadata_file)
                        if not self.__file_in_target_service(file_path):
                            continue
                        violations = []
                        if '/alarm/' in file_path:
                            violations = pd.get_metadata_violations(document_metadata, file_path,
                                                                    meta_attrs_map.get('alarm'))
                        elif '/test/' in file_path:
                            violations = pd.get_metadata_violations(document_metadata, file_path,
                                                                    meta_attrs_map.get('test'))
                        elif '/sop/' in file_path:
                            violations = pd.get_metadata_violations(document_metadata, file_path,
                                                                    meta_attrs_map.get('sop'))
                        fail_messages.extend(violations)
                        global_metadata_validator.iterate_file(document_metadata, file_path)

        fail_messages.extend(global_metadata_validator.get_metadata_violations())
        for msg in fail_messages:
            logging.error(msg)
        if len(fail_messages) > 0:
            raise Exception("Detected [{}] metadata.json structural violations.".format(len(fail_messages)))

    @pytest.mark.style_validator
    @pytest.mark.ssm_document_validator
    def test_validate_automation_document(self):
        existing_services = ['sqs', 'docdb', 'lambda', 's3', 'nat-gw']
        fail_messages = []
        warn_messages = []
        for root, dirs, files in os.walk("documents"):
            if "not_completed" in dirs:
                dirs.remove('not_completed')
            if "util" in dirs:
                dirs.remove('util')

            document_validator = DocumentValidator()
            for f in files:
                if f == 'AutomationDocument.yml':
                    with open(os.path.join(root, f)) as automation_file:
                        file_path = os.path.join(root, f)
                        if not self.__file_in_target_service(file_path):
                            continue
                        automation_document = yaml.safe_load(automation_file)
                        service = file_path.split('/')[1]
                        violations = document_validator.validate_document(automation_document, file_path)
                        if service in existing_services:
                            warn_messages.extend(violations)
                        else:
                            fail_messages.extend(violations)

        logging.info("Detected [{}] WARN and [{}] ERROR structural violations"
                     .format(len(warn_messages), len(fail_messages)))
        for msg in warn_messages:
            logging.warning(msg)
        for msg in fail_messages:
            logging.error(msg)
        if len(fail_messages) > 0:
            raise Exception("Detected [{}] ERROR structural violations.".format(len(fail_messages)))

    def __file_in_target_service(self, file_path):
        return (not self.target_service) or '/' + self.target_service + '/' in file_path
