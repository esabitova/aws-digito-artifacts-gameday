import unittest
from unittest.mock import patch, MagicMock

import pytest

from adk.src.adk.builtin_steps.automation.run_commands import run_shell_script


@pytest.mark.unit_test
class TestRunCommandStep(unittest.TestCase):

    def setUp(self):
        self.patcher = patch('boto3.client')
        self.client = self.patcher.start()
        self.mock_ssm = MagicMock()
        self.side_effect_map = {
            'ssm': self.mock_ssm
        }
        self.mock_ssm.get_command_invocation.return_value = {'Status': 'Success', 'ResponseCode': 0}
        self.mock_ssm.send_command.return_value = {'Command': {'CommandId': 'Command1234'}}
        self.client.side_effect = lambda service_name, config=None: self.side_effect_map.get(service_name)

    def tearDown(self):
        self.patcher.stop()

    @patch('subprocess.run')
    def test_should_invoke_locally(self, mocked_subprocess):
        run_command = run_shell_script(use_send_command=False, commands=['echo foobar', 'echo again'],
                                       instance_ids_input='InstId')
        run_command.invoke({'InstId': 'i-12341234'})
        mocked_subprocess.assert_called_with("cd \necho foobar\necho again",
                                             capture_output=True, shell=True, timeout=3600)

    def test_should_call_send_command(self):
        run_command = run_shell_script(use_send_command=True, commands=['echo foobar'], instance_ids_input='InstId')
        run_command.invoke({'InstId': 'i-12341234'})
        self.mock_ssm.send_command.assert_called_with(
            InstanceIds=['i-12341234'],
            DocumentName='AWS-RunShellScript',
            Parameters={'commands': ['echo foobar'], 'workingDirectory': [''], 'executionTimeout': ['3600']})

    def test_automation_step_yaml(self):
        step_yaml = run_shell_script(["echo foobar"], instance_ids_input='InstId').get_yaml()
        self.assertEqual('description: \'Command Document: AWS_RunShellScript\'\n'
                         'name: AWS_RunShellScript\n'
                         'action: aws:runCommand\n'
                         'inputs:\n'
                         '  DocumentName: AWS-RunShellScript\n'
                         '  InstanceIds:\n'
                         '  - \'{{ InstId }}\'\n'
                         '  Parameters:\n'
                         '    commands:\n'
                         '    - echo foobar\n', step_yaml)

    def test_command_doc_yaml(self):
        step_yaml = run_shell_script(["echo foobar"], instance_ids_input='InstId').get_document_yaml()
        self.assertEqual(
            'description: \'Command Document: AWS_RunShellScript\'\n'
            'schemaVersion: \'2.2\'\n'
            'parameters:\n'
            '  commands:\n'
            '    type: StringList\n'
            '    description: desc\n'
            '  workingDirectory:\n'
            '    type: String\n'
            '    description: desc\n'
            '    default: \'\'\n'
            '  executionTimeout:\n'
            '    type: String\n'
            '    description: desc\n'
            '    default: \'3600\'\n'
            'mainSteps:\n'
            '- name: MyRunShell\n'
            '  action: aws:runShellScript\n'
            '  inputs:\n'
            '    runCommand:\n'
            '    - \'{{ commands }}\'\n'
            '    workingDirectory: \'{{ workingDirectory }}\'\n'
            '    timeoutSeconds: \'{{ executionTimeout }}\'\n', step_yaml)
