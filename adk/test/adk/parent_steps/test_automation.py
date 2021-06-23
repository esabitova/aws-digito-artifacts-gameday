import unittest
from unittest.mock import patch, MagicMock

import pytest

from adk.src.adk.domain.branch_operation import Operation
from adk.src.adk.domain.cancellation_exception import CancellationException
from adk.src.adk.domain.choice import Choice
from adk.src.adk.domain.non_retriable_exception import NonRetriableException
from adk.src.adk.parent_steps.branch_step import BranchStep
from adk.src.adk.parent_steps.sleep_step import SleepStep
from adk.src.adk.steps.aws_api.ec2_repo import get_ec2_describe_instances
from adk.src.adk.steps.wait_for_resource.ec2_repo import get_wait_for_instance_start
from adk.src.adk.steps.sample_step import SampleStep
from adk.src.adk.domain.data_type import DataType
from adk.src.adk.domain.input import Input
from adk.src.adk.parent_steps.automation import Automation
from adk.src.adk.parent_steps.pause_step import PauseStep


@pytest.mark.unit_test
class TestAutomation(unittest.TestCase):

    def setUp(self):
        self.patcher = patch('boto3.client')
        self.client = self.patcher.start()
        self.mock_autoscaling = MagicMock()
        self.mock_ec2 = MagicMock()
        self.side_effect_map = {
            'autoscaling': self.mock_autoscaling,
            'ec2': self.mock_ec2
        }
        self.client.side_effect = lambda service_name, config=None: self.side_effect_map.get(service_name)

        self.automation_step = Automation(
            name="AssertEc2Running",
            steps=[PauseStep(pause_runtime=True)],
            assume_role='AutoRole',
            inputs=[Input(name='AutoRole', input_type=DataType.String, description="role"),
                    Input(name="SampleInput", input_type=DataType.String, description="Sample",
                          allowed_values=["One", "Two"])])
        self.automation_step_wo_output = Automation(
            name="AssertEc2Running",
            steps=[PauseStep(pause_runtime=True)],
            assume_role='AutoRole',
            inputs=[Input(name='AutoRole', input_type=DataType.String, description="role")])

    def tearDown(self):
        self.patcher.stop()

    @patch('adk.src.adk.parent_steps.pause_step.PauseStep.get_input')
    def test_automation_should_recursively_call_steps(self, mocked_pause):
        self.automation_step_wo_output.invoke(
            {'AutoRole': 'SudoAdminSuperRole', 'SampleInput': "One", 'SampleInput2': 'asdf'})
        mocked_pause.assert_called_once()

    def test_automation_step_yaml(self):
        self.assertEqual(
            'description: \'Execute another SSM Doc: AssertEc2Running\'\n'
            'name: AssertEc2Running\n'
            'action: aws:executeAutomation\n'
            'inputs:\n'
            '  DocumentName: AssertEc2Running\n'
            '  RuntimeParameters:\n'
            '    AutoRole: \'{{ AutoRole }}\'\n'
            '    SampleInput: \'{{ SampleInput }}\'\n', self.automation_step.get_yaml())

    def test_automation_doc_yaml(self):
        self.assertEqual('description: \'SOP By Digito: AssertEc2Running\'\n'
                         'schemaVersion: \'0.3\'\n'
                         'assumeRole: \'{{AutoRole}}\'\n'
                         'parameters:\n'
                         '  AutoRole:\n'
                         '    type: String\n'
                         '    description: role\n'
                         '  SampleInput:\n'
                         '    type: String\n'
                         '    description: Sample\n'
                         '    allowedValues:\n'
                         '    - One\n'
                         '    - Two\n'
                         'mainSteps:\n'
                         '- name: PauseStep\n'
                         '  action: aws:pause\n'
                         '  inputs: {}\n'
                         , self.automation_step.get_automation_yaml())

    def test_allowed_values_validation(self):
        input_data = {'AutoRole': 'SudoAdminSuperRole', 'SampleInput': "Three", 'SampleInput2': 'asdf'}
        self.assertRaises(Exception, self.automation_step.run_automation, input_data)

    @patch('time.sleep', return_value=None)
    def test_simulate_multi_step_ssm(self, patched_time_sleep):
        ssm_doc: Automation = sample_ssm()

        self.mock_ec2.describe_instances.return_value = {'Reservations': [{'Instances': [
            {'InstanceType': 't1.nano', 'State': {'Name': 'running'}}]}]}

        ssm_output = ssm_doc.run_automation(
            {"InstanceId": 'i-0acf3aed3b36c6f51', 'AutomationAssumeRole': 'bienenfeAsgFull', 'DryRun': False})
        self.assertEqual('barValt1.nanoSome Amazing Value', ssm_output['SampleStep.Bar'])
        self.assertEqual(['Ec2DescribeInstances', 'BranchForSomething', 'SampleStep',
                          'WaitForInstanceStart', 'AnotherStep', 'SleepStep'], ssm_output["python_simulation_steps"])

    @patch('time.sleep', return_value=None)
    def test_on_cancel(self, patched_time):
        ssm_doc: Automation = sample_ssm()

        self.mock_ec2.describe_instances.side_effect = CancellationException("Canceled in mock")
        ssm_output = ssm_doc.run_automation(
            {"InstanceId": 'i-0acf3aed3b36c6f51', 'AutomationAssumeRole': 'bienenfeAsgFull', 'DryRun': False})
        self.assertIsNone(ssm_output.get('SampleStep.Bar'))
        self.assertEqual(['Ec2DescribeInstances', 'SleepStep'], ssm_output["python_simulation_steps"])

    @patch('time.sleep', return_value=None)
    def test_on_failure(self, patched_time):
        # Pause will not get called...
        ssm_doc: Automation = sample_ssm()

        self.mock_ec2.describe_instances.side_effect = [{'Reservations': [{'Instances': [
            {'InstanceType': 't1.nano', 'State': {'Name': 'running'}}]}]},
            {'Reservations': [{'Instances': [
                {'InstanceType': 't1.nano', 'State': {'Name': 'running'}}]}]},
            NonRetriableException("Canceled in mock")]
        ssm_output = ssm_doc.run_automation(
            {"InstanceId": 'i-0acf3aed3b36c6f51', 'AutomationAssumeRole': 'bienenfeAsgFull', 'DryRun': False})
        self.assertIsNotNone(ssm_output.get('SampleStep.Bar'))
        self.assertEqual(['Ec2DescribeInstances', 'BranchForSomething', 'SampleStep',
                          'WaitForInstanceStart', 'SleepStep'], ssm_output["python_simulation_steps"])

    def test_print_multi_step_ssm(self):
        ssm_doc = sample_ssm()

        self.assertEqual(
            'description: \'SOP By Digito: SampleStep\'\n'
            'schemaVersion: \'0.3\'\n'
            'assumeRole: \'{{AutomationAssumeRole}}\'\n'
            'parameters:\n'
            '  InstanceId:\n'
            '    type: String\n'
            '    description: Your instance id\n'
            '  AutomationAssumeRole:\n'
            '    type: String\n'
            '    description: The role to assume\n'
            '  DryRun:\n'
            '    type: Boolean\n'
            '    description: Dryrun indication\n'
            'outputs:\n'
            '- SampleStep.Foo\n'
            'mainSteps:\n'
            '- description: Describes EC2 Instance\n'
            '  name: Ec2DescribeInstances\n'
            '  action: aws:executeAwsApi\n'
            '  inputs:\n'
            '    Service: ec2\n'
            '    Api: DescribeInstances\n'
            '    Filters:\n'
            '    - Name: instance-id\n'
            '      Values:\n'
            '      - \'{{ InstanceId }}\'\n'
            '  outputs:\n'
            '  - Name: InstanceType\n'
            '    Selector: $.Reservations[0].Instances[0].InstanceType\n'
            '    Type: String\n'
            '  - Name: State\n'
            '    Selector: $.Reservations[0].Instances[0].State.Name\n'
            '    Type: String\n'
            '  onCancel: step:SleepStep\n'
            '- description: Branch based on DryRun\n'
            '  name: BranchForSomething\n'
            '  action: aws:branch\n'
            '  inputs:\n'
            '    Choices:\n'
            '    - NextStep: SleepStep\n'
            '      Variable: \'{{DryRun}}\'\n'
            '      BooleanEquals: true\n'
            '- description: Description for the step (markdown)\n'
            '  name: SampleStep\n'
            '  action: aws:executeScript\n'
            '  inputs:\n'
            '    Runtime: python3.6\n'
            '    Handler: script_handler\n'
            '    Script: |\n'
            '      import time\n'
            '      import boto3\n'
            '\n'
            '      def script_handler(params: dict, context) -> dict:\n'
            '          """\n'
            '          Implementation of script used in aws:executeScript.\n'
            '          :param params: input params (will include the params requested in get_inputs())\n'
            '          :param context: None. Not used (but necessary for SSM)\n'
            '          :return: dict with all of the outputs declared. DO NOT include Payload.\n'
            '          """\n'
            '          # Do complicated things... and then...\n'
            '          return helper_func(params)\n'
            '\n'
            '      def helper_func(params: dict):\n'
            '          # This is a comment\n'
            '          client = boto3.client(\'ec2\')\n'
            '          client.describe_instances()\n'
            '          time.sleep(1)\n'
            '\n'
            '          return {\n'
            '              "Foo": 4,\n'
            '              "Bar": "barVal" + params[\'InstanceType\'] + amazing_function()\n'
            '          }\n'
            '\n'
            '      def amazing_function():\n'
            '          return "Some Amazing Value"\n'
            '    InputPayload:\n'
            '      InstanceType: \'{{ Ec2DescribeInstances.InstanceType }}\'\n'
            '  outputs:\n'
            '  - Name: Foo\n'
            '    Selector: $.Payload.Foo\n'
            '    Type: Integer\n'
            '  - Name: Bar\n'
            '    Selector: $.Payload.Bar\n'
            '    Type: String\n'
            '  maxAttempts: 3\n'
            '- description: Waits for instance to start running\n'
            '  name: WaitForInstanceStart\n'
            '  action: aws:waitForAwsResourceProperty\n'
            '  inputs:\n'
            '    Service: ec2\n'
            '    Api: DescribeInstances\n'
            '    PropertySelector: $.Reservations[0].Instances[0].State.Name\n'
            '    DesiredValues:\n'
            '    - running\n'
            '    - going\n'
            '    Filters:\n'
            '    - Name: instance-id\n'
            '      Values:\n'
            '      - \'{{ InstanceId }}\'\n'
            '  onFailure: step:SleepStep\n'
            '- description: \'Execute another SSM Doc: AnotherStep\'\n'
            '  name: AnotherStep\n'
            '  action: aws:executeAutomation\n'
            '  inputs:\n'
            '    DocumentName: AnotherStep\n'
            '    RuntimeParameters:\n'
            '      AutomationAssumeRole: \'{{ AutomationAssumeRole }}\'\n'
            '- name: SleepStep\n'
            '  action: aws:sleep\n'
            '  inputs:\n'
            '    Duration: PT1S\n', ssm_doc.get_automation_yaml())


def another_ssm() -> Automation:
    return Automation(inputs=[
        Input(name="AutomationAssumeRole", input_type=DataType.String, description="The role to assume")
    ],
        assume_role='AutomationAssumeRole',
        steps=[
            PauseStep(pause_runtime=False),
    ],
        name="AnotherStep")


def sample_ssm() -> Automation:
    final_step = SleepStep(sleep_seconds=1)
    return Automation(inputs=[
        Input(name="InstanceId", input_type=DataType.String, description="Your instance id"),
        Input(name="AutomationAssumeRole", input_type=DataType.String, description="The role to assume"),
        Input(name="DryRun", input_type=DataType.Boolean, description="Dryrun indication")
    ],
        doc_outputs=["SampleStep.Foo"],
        assume_role="AutomationAssumeRole",
        steps=[
            get_ec2_describe_instances().on_cancel(final_step),
            BranchStep(name="BranchForSomething", description="Branch based on DryRun", choices=[
                Choice(skip_to=final_step, input_to_test='DryRun', operation=Operation.BooleanEquals, constant=True)]),
            SampleStep().max_attempts(3),
            get_wait_for_instance_start().on_failure(final_step),
            another_ssm(),
            final_step
    ],
        name="SampleStep")
