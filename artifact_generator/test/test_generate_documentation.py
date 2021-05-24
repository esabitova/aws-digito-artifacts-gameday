import pytest
import unittest
import os
import pathlib
from unittest.mock import patch, Mock, mock_open
from artifact_generator.src.generate_documentation import main, DocumentationInfo
from mako.lookup import Template
import yaml
import json
from cfn_tools import load_yaml


@pytest.mark.unit_test
@patch('artifact_generator.src.generate_documentation.os.walk')
@patch('artifact_generator.src.generate_documentation.template_lookup')
class TestGenerateDocumentation(unittest.TestCase):

    with open(os.path.join(pathlib.Path(__file__).parent, 'resources/AutomationDocument.yml'), 'r') as f:
        automation_doc = f.read()
        automation_doc_yaml = yaml.safe_load(automation_doc)
    with open(os.path.join(pathlib.Path(__file__).parent, 'resources/metadata.json'), 'r') as f:
        metadata_doc = f.read()
        metadata_doc_json = json.loads(metadata_doc)
    with open(os.path.join(pathlib.Path(__file__).parent, 'resources/metadataForUtil.json'), 'r') as f:
        metadata_util_doc = f.read()
        metadata_util_doc_json = json.loads(metadata_util_doc)
    with open(os.path.join(pathlib.Path(__file__).parent, 'resources/AutomationAssumeRoleTemplate.yml'), 'r') as f:
        role_doc = f.read()
        role_doc_yaml = load_yaml(role_doc)
    mock_template = Mock(Template)

    def setup(self, mock_open, mock_lookup):
        mock_lookup.get_template.return_value = self.mock_template
        mock_open.side_effect = self.__open_side_effect

    @patch('builtins.open')
    def test_generate_for_test(self, mock_open, mock_lookup, mock_os_walk):
        mock_os_walk.return_value = [
            ('documents/my-service/test/my_test/2021-05-04', ['Documents', 'Tests'],
             ['metadata.json', 'AutomationDocument.yml', 'AutomationAssumeRoleTemplate.yml'])]
        self.setup(mock_open, mock_lookup)
        main()
        actual_doc_info: DocumentationInfo = self.mock_template.render.call_args[1].get('doc_info')
        expected_doc_info: DocumentationInfo = DocumentationInfo('my-service:test:my_test:2021-05-04', 'test',
                                                                 self.metadata_doc_json, self.automation_doc_yaml,
                                                                 self.role_doc_yaml)
        assert expected_doc_info == actual_doc_info

    @patch('builtins.open')
    def test_generate_for_util(self, mock_open, mock_lookup, mock_os_walk):
        mock_os_walk.return_value = [('documents/util/my-service/my_util/2021-05-04',
                                      ['Documents'], ['metadata.json', 'AutomationDocument.yml'])]
        self.setup(mock_open, mock_lookup)
        main()
        actual_doc_info: DocumentationInfo = self.mock_template.render.call_args[1].get('doc_info')
        expected_doc_info: DocumentationInfo = DocumentationInfo('my-service:util:my_util:2021-05-04', 'util',
                                                                 self.metadata_util_doc_json, self.automation_doc_yaml,
                                                                 None)
        assert expected_doc_info == actual_doc_info

    def __open_side_effect(self, *args):
        if 'AutomationDocument.yml' in args[0]:
            return mock_open(read_data=self.automation_doc).return_value
        if 'metadata.json' in args[0]:
            if 'util' in args[0]:
                return mock_open(read_data=self.metadata_util_doc).return_value
            else:
                return mock_open(read_data=self.metadata_doc).return_value
        if 'AutomationAssumeRoleTemplate.yml' in args[0]:
            return mock_open(read_data=self.role_doc).return_value
        return mock_open(read_data='').return_value
