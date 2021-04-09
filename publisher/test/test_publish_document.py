import unittest
import pytest
import os
import logging
import json
from publisher.src.publish_documents import PublishDocuments
import publisher.src.document_metadata_attrs as metadata_attrs
import boto3


@pytest.mark.metadata_validator
class TestPublishDocuments(unittest.TestCase):

    def test_validate_metadata_files(self):
        pd = PublishDocuments(boto3.Session())
        meta_attrs_map = metadata_attrs.metadata_attrs_map
        fail_messages = []
        for root, dirs, files in os.walk("documents"):
            if "not_completed" in dirs:
                dirs.remove('not_completed')
            if "util" in dirs:
                dirs.remove('util')

            for f in files:
                if f == 'metadata.json':
                    with open(os.path.join(root, f)) as metadata_file:
                        document_metadata = json.load(metadata_file)
                        file_path = os.path.join(root, f)
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

        for msg in fail_messages:
            logging.error(msg)
        if len(fail_messages) > 0:
            raise Exception("Detected [{}] metadata.json structural violations.".format(len(fail_messages)))
