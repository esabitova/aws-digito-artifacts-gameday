import pytest
import unittest
import os
import pathlib
import re
from unittest.mock import patch, call, ANY, Mock, mock_open
from artifact_generator.src.generate_artifacts import main
from mako.lookup import Template


@pytest.mark.unit_test
@patch('artifact_generator.src.generate_artifacts.os.path.isdir')
@patch('artifact_generator.src.generate_artifacts.os.makedirs')
@patch('artifact_generator.src.generate_artifacts.os.path.isfile')
@patch('builtins.open')
@patch('artifact_generator.src.generate_artifacts.re.sub')
@patch('artifact_generator.src.generate_artifacts.template_lookup')
class TestGenerateArtifacts(unittest.TestCase):
    SERVICE_NAME = 'my-service'
    SERVICE_NAME_PASCAL_CASE = 'MyService'
    TEST_DOC_TYPE = 'test'
    SOP_DOC_TYPE = 'sop'
    TEST_NAME = 'my_test'
    TEST_NAME_PASCAL_CASE = 'MyTest'
    SOP_NAME = 'my_sop'
    SOP_NAME_PASCAL_CASE = 'MySop'
    DATE = '2021-05-04'
    DISPLAY_NAME = 'My Display Name'
    DESCRIPTION = 'My Description'
    RESOURCE_ID = 'ResourceId'
    RESOURCE_ID_CFN_OUTPUT = 'ResourceIdOutput'
    FAILURE_TYPE = 'SOFTWARE'
    RISK = 'HIGH'
    ALARM_PREFIX = 'UserError'
    ALARM_CFN_OUTPUT = ALARM_PREFIX + 'AlarmNameOutput'
    ALARM_ID = 'my-service:alarm:user-error:2021-05-04'
    RECOVERY_POINT_STEP = 'CalculateRecoveryPoint'
    CFN_TEMPLATE_NAME = 'MyServiceTemplate'
    SSM_TEST_DOC_NAME = "Digito-{}_{}".format(TEST_NAME_PASCAL_CASE, DATE)
    SSM_SOP_DOC_NAME = "Digito-{}_{}".format(SOP_NAME_PASCAL_CASE, DATE)

    expected_replacements_common = {
        '${serviceName}': SERVICE_NAME,
        '${date}': DATE,
        '${displayName}': DISPLAY_NAME,
        '${description}': DESCRIPTION,
        '${assumeRoleCfnPath}': 'AutomationAssumeRoleTemplate.yml',
        '${documentContentPath}': 'AutomationDocument.yml',
        '${failureType}': FAILURE_TYPE,
        '${risk}': RISK,
        '${primaryResourceIdentifier}': RESOURCE_ID,
        '${cfnTemplateName}': CFN_TEMPLATE_NAME,
        '${resourceIdOutput}': RESOURCE_ID_CFN_OUTPUT
    }
    expected_replacements_test = {**expected_replacements_common,
                                  '${documentName}': SSM_TEST_DOC_NAME,
                                  '${documentType}': TEST_DOC_TYPE,
                                  '${name}': TEST_NAME,
                                  '${tag}': ":".join([SERVICE_NAME, TEST_DOC_TYPE, TEST_NAME, DATE]),
                                  '${roleName}': "Digito{}{}AssumeRole".format(SERVICE_NAME_PASCAL_CASE,
                                                                               TEST_NAME_PASCAL_CASE),
                                  '${policyName}': "Digito{}{}AssumePolicy".format(SERVICE_NAME_PASCAL_CASE,
                                                                                   TEST_NAME_PASCAL_CASE),
                                  '${alarmNameOutput}': ALARM_CFN_OUTPUT}
    expected_replacements_sop = {**expected_replacements_common,
                                 '${documentName}': SSM_SOP_DOC_NAME,
                                 '${documentType}': SOP_DOC_TYPE,
                                 '${name}': SOP_NAME,
                                 '${tag}': ":".join([SERVICE_NAME, SOP_DOC_TYPE, SOP_NAME, DATE]),
                                 '${roleName}': "Digito{}{}AssumeRole".format(SERVICE_NAME_PASCAL_CASE,
                                                                              SOP_NAME_PASCAL_CASE),
                                 '${policyName}': "Digito{}{}AssumePolicy".format(SERVICE_NAME_PASCAL_CASE,
                                                                                  SOP_NAME_PASCAL_CASE),
                                 '${alarmNameOutput}': ''}
    scenario_name = 'Scenario: Execute SSM automation document'

    re_sub_side_effects = {('_test|_sop', '', 'usual_case_sop.feature'): 'usual_case.feature',
                           ('_test|_sop', '', 'usual_case_test.feature'): 'usual_case.feature',
                           ('_test|_sop', '', 'failed.feature'): 'failed.feature',
                           ('_test|_sop', '', 'rollback_previous.feature'): 'rollback_previous.feature'}
    package_dir = pathlib.Path(__file__).parent.parent.parent.absolute()
    templates_path = os.path.join(pathlib.Path(__file__).parent.parent, 'src', 'templates')

    input_for_test = [SERVICE_NAME, TEST_DOC_TYPE, TEST_NAME, DATE, DISPLAY_NAME, DESCRIPTION, RESOURCE_ID,
                      FAILURE_TYPE, RISK, 'yes', 'no', ALARM_PREFIX, ALARM_ID, CFN_TEMPLATE_NAME,
                      RESOURCE_ID_CFN_OUTPUT, ALARM_CFN_OUTPUT, 'no']
    input_for_test_synth_alarm = [SERVICE_NAME, TEST_DOC_TYPE, TEST_NAME, DATE, DISPLAY_NAME, DESCRIPTION,
                                  RESOURCE_ID, FAILURE_TYPE, RISK, 'yes', 'yes', CFN_TEMPLATE_NAME,
                                  RESOURCE_ID_CFN_OUTPUT, ALARM_CFN_OUTPUT, 'no']
    input_for_test_no_rollback = [SERVICE_NAME, TEST_DOC_TYPE, TEST_NAME, DATE, DISPLAY_NAME, DESCRIPTION, RESOURCE_ID,
                                  FAILURE_TYPE, RISK, 'no', 'no', ALARM_PREFIX, ALARM_ID, CFN_TEMPLATE_NAME,
                                  RESOURCE_ID_CFN_OUTPUT, ALARM_CFN_OUTPUT, 'no']
    input_for_sop = [SERVICE_NAME, SOP_DOC_TYPE, SOP_NAME, DATE, DISPLAY_NAME, DESCRIPTION, RESOURCE_ID, FAILURE_TYPE,
                     RISK, 'yes', RECOVERY_POINT_STEP, CFN_TEMPLATE_NAME,
                     RESOURCE_ID_CFN_OUTPUT, 'no']

    @patch('builtins.input', side_effect=[SERVICE_NAME, TEST_DOC_TYPE, TEST_NAME, DATE, 'no'])
    def test_no_overwrite(self, mock_inputs, mock_lookup, mock_re_sub, mock_open, mock_is_file, mock_mkdir,
                          mock_is_dir):
        mock_is_dir.return_value = True
        mock_is_file.return_value = True
        with pytest.raises(SystemExit) as e:
            main()
        assert e.type == SystemExit
        assert e.value.code == 0
        mock_mkdir.assert_not_called()
        mock_re_sub.assert_not_called()
        mock_open.assert_not_called()

    @patch('builtins.input', side_effect=[SERVICE_NAME, SOP_DOC_TYPE, SOP_NAME, DATE, DISPLAY_NAME, DESCRIPTION,
                                          RESOURCE_ID, FAILURE_TYPE, RISK, 'yes', RECOVERY_POINT_STEP,
                                          CFN_TEMPLATE_NAME, RESOURCE_ID_CFN_OUTPUT, 'yes'])
    def test_generate_cfn_template(self, mock_inputs, mock_lookup, mock_re_sub, mock_open, mock_is_file,
                                   mock_mkdir, mock_is_dir):
        mock_is_dir.return_value = False
        mock_is_file.return_value = False
        mock_re_sub.side_effect = self.__re_sub_side_effect
        main()
        mock_open.assert_has_calls([
            call(os.path.join(self.templates_path, 'CloudFormationTemplate.yml'), 'r'),
            call(os.path.join(os.path.join(self.package_dir, "resource_manager", "cloud_formation_templates"),
                              self.CFN_TEMPLATE_NAME + '.yml'), 'w')], any_order=True)

    @patch('builtins.input', side_effect=input_for_test)
    def test_generate_test_with_recommended_alarm(self, mock_inputs, mock_lookup, mock_re_sub, mock_open, mock_is_file,
                                                  mock_mkdir, mock_is_dir):
        expected_replacements = {}
        expected_replacements.update(self.expected_replacements_test)
        expected_replacements['${alarmPrefix}'] = self.ALARM_PREFIX
        expected_replacements['${recommendedAlarms}'] = ',\n  "recommendedAlarms": {{ "{}AlarmName": "{}" }}'\
            .format(self.ALARM_PREFIX, self.ALARM_ID)
        self.__generate_and_validate(mock_lookup, mock_re_sub, mock_open, mock_is_file, mock_mkdir, mock_is_dir,
                                     expected_replacements, 'AutomationDocumentForTest.yml',
                                     ['usual_case_test.feature', 'failed.feature', 'rollback_previous.feature'])

    @patch('builtins.input', side_effect=input_for_test_synth_alarm)
    def test_generate_test_synth_alrm(self, mock_inputs, mock_lookup, mock_re_sub, mock_open, mock_is_file, mock_mkdir,
                                      mock_is_dir):
        expected_replacements = {}
        expected_replacements.update(self.expected_replacements_test)
        expected_replacements['${alarmPrefix}'] = 'Synthetic'
        expected_replacements['${recommendedAlarms}'] = ''
        self.__generate_and_validate(mock_lookup, mock_re_sub, mock_open, mock_is_file, mock_mkdir, mock_is_dir,
                                     expected_replacements, 'AutomationDocumentForTest.yml',
                                     ['usual_case_test.feature', 'failed.feature', 'rollback_previous.feature'])

    @patch('builtins.input', side_effect=input_for_test_no_rollback)
    def test_generate_test_no_rollbck(self, mock_inputs, mock_lookup, mock_re_sub, mock_open, mock_is_file, mock_mkdir,
                                      mock_is_dir):
        expected_replacements = {}
        expected_replacements.update(self.expected_replacements_test)
        expected_replacements['${alarmPrefix}'] = self.ALARM_PREFIX
        expected_replacements['${recommendedAlarms}'] = ',\n  "recommendedAlarms": {{ "{}AlarmName": "{}" }}' \
            .format(self.ALARM_PREFIX, self.ALARM_ID)
        self.__generate_and_validate(mock_lookup, mock_re_sub, mock_open, mock_is_file, mock_mkdir, mock_is_dir,
                                     expected_replacements, 'AutomationDocumentForTestNoRollback.yml',
                                     ['usual_case_test.feature'])

    @patch('builtins.input', side_effect=input_for_sop)
    def test_generate_sop(self, mock_inputs, mock_lookup, mock_re_sub, mock_open, mock_is_file, mock_mkdir,
                          mock_is_dir):
        expected_replacements = {}
        expected_replacements.update(self.expected_replacements_sop)
        expected_replacements['${recoveryPointStep}'] = '- name: {} # step that calculates the recovery point'\
            .format(self.RECOVERY_POINT_STEP)
        expected_replacements['${recoveryPointOutput}'] = '- {}.RecoveryPoint'.format(self.RECOVERY_POINT_STEP)
        expected_replacements['${recommendedAlarms}'] = ''
        self.__generate_and_validate(mock_lookup, mock_re_sub, mock_open, mock_is_file, mock_mkdir, mock_is_dir,
                                     expected_replacements, 'AutomationDocumentForSop.yml', ['usual_case_sop.feature'])

    def __generate_and_validate(self, mock_lookup, mock_re_sub, mock_open, mock_is_file, mock_mkdir, mock_is_dir,
                                expected_replacements: dict, automation_template: str,
                                feature_templates: list):
        mock_template = Mock(Template)
        mock_is_dir.return_value = False
        mock_is_file.return_value = False
        mock_re_sub.side_effect = self.__re_sub_side_effect
        mock_open.side_effect = self.__open_side_effect
        mock_lookup.get_template.return_value = mock_template
        main()

        artifacts_dir = os.path.join(self.package_dir, 'documents', expected_replacements['${serviceName}'],
                                     expected_replacements['${documentType}'], expected_replacements['${name}'],
                                     expected_replacements['${date}'])
        documents_path = os.path.join(artifacts_dir, 'Documents')
        features_path = os.path.join(artifacts_dir, 'Tests', 'features')
        step_def_path = os.path.join(artifacts_dir, 'Tests', 'step_defs')

        mock_mkdir.assert_has_calls([call(documents_path), call(features_path), call(step_def_path)])
        mock_re_sub.assert_has_calls([call(re.escape(k), v, ANY) for k, v in expected_replacements.items()],
                                     any_order=True)

        mock_open.assert_has_calls([
            call(os.path.join(self.templates_path, 'metadata.json'), 'r'),
            call(os.path.join(documents_path, 'metadata.json'), 'w'),
            call(os.path.join(self.templates_path, 'AutomationAssumeRoleTemplate.yml'), 'r'),
            call(os.path.join(documents_path, 'AutomationAssumeRoleTemplate.yml'), 'w'),
            call(os.path.join(self.templates_path, automation_template), 'r'),
            call(os.path.join(documents_path, 'AutomationDocument.yml'), 'w')], any_order=True)

        target_feature_files = []
        for f in feature_templates:
            feature_path = os.path.join(features_path, '{}_{}'.format(expected_replacements['${name}'],
                                                                      f.replace('_test', '').replace('_sop', '')))
            mock_open.assert_has_calls([call(os.path.join(self.templates_path, f), 'r'),
                                        call(feature_path, 'w')], any_order=True)
            mock_open.assert_has_calls([call(os.path.join(self.templates_path, f), 'r'),
                                        call(feature_path, 'r')], any_order=True)
            target_feature_files.append(feature_path)
        mock_open.assert_has_calls([call(os.path.join(step_def_path,
                                                      'test_{}.py'.format(expected_replacements['${name}']
                                                                          .replace('-', '_'))), 'w')], any_order=True)

        self.__assert_step_def_replacement(mock_lookup, mock_template, step_def_path, target_feature_files)

    def __assert_step_def_replacement(self, mock_lookup, mock_template, step_def_path, feature_files):
        mock_lookup.get_template.assert_called_once_with("step_def.py.mak")
        mock_template.render.assert_called_once()
        # validate that the scenario names are as expected
        actual_scenarios = set([s.name for s in mock_template.render.call_args[1]['scenarios']])
        expected_scenario = self.scenario_name.replace('Scenario:', '').strip()
        assert len(actual_scenarios) == 1
        assert expected_scenario == actual_scenarios.pop()
        # validate feature file paths in scenarios are as expected
        actual_scenario_feature_files = [s.feature_file for s in mock_template.render.call_args[1]['scenarios']]
        expected_scenario_feature_files = [os.path.relpath(s, step_def_path) for
                                           s in feature_files]
        self.assertCountEqual(actual_scenario_feature_files, expected_scenario_feature_files)

    def __re_sub_side_effect(self, *args):
        if args in self.re_sub_side_effects:
            return self.re_sub_side_effects[args]
        return unittest.mock.DEFAULT

    def __open_side_effect(self, *args):
        if '/features/' in args[0]:
            return mock_open(read_data=self.scenario_name).return_value
        return mock_open(read_data='').return_value
