import pytest
import unittest
import logging
import os
import pathlib
from unittest.mock import patch, call
from artifact_generator.src.generate_artifacts import main


@pytest.mark.unit_test
@patch('artifact_generator.src.generate_artifacts.os.path.isdir')
@patch('artifact_generator.src.generate_artifacts.os.makedirs')
@patch('artifact_generator.src.generate_artifacts.os.path.isfile')
@patch('builtins.open')
@patch('artifact_generator.src.generate_artifacts.re')
class TestGenerateArtifacts(unittest.TestCase):
    SERVICE_NAME = 'my-service'
    SERVICE_NAME_PASCAL_CASE = 'MyService'
    TEST_DOC_TYPE = 'test'
    SOP_DOC_TYPE = 'sop'
    TEST_NAME = 'my_test'
    TEST_NAME_PASCAL_CASE = 'MyTest'
    SOP_NAME = 'my_sop'
    DATE = '2021-05-04'
    DISPLAY_NAME = 'My Display Name'
    DESCRIPTION = 'My Description'
    RESOURCE_ID = 'ResourceId'
    FAILURE_TYPE = 'SOFTWARE'
    RISK = 'HIGH'
    ALARM_PREFIX = 'UserError'
    ALARM_ID = 'my-service:alarm:user-error:2021-05-04'
    RECOVERY_POINT_STEP = 'CalculateRecoveryPoint'

    expected_replacements_common = {
        '${displayName}': DISPLAY_NAME,
        '${description}': DESCRIPTION,
        '${assumeRoleCfnPath}': 'AutomationAssumeRoleTemplate.yml',
        '${documentContentPath}': 'AutomationDocument.yml',
        '${documentName}': "Digito-{}_{}".format(TEST_NAME_PASCAL_CASE, DATE),
        '${failureType}': FAILURE_TYPE,
        '${risk}': RISK,
        '${tag}': ":".join([SERVICE_NAME, TEST_DOC_TYPE, TEST_NAME, DATE]),
        '${roleName}': "Digito{}{}AssumeRole".format(SERVICE_NAME_PASCAL_CASE,
                                                     TEST_NAME_PASCAL_CASE),
        '${policyName}': "Digito{}{}AssumePolicy".format(SERVICE_NAME_PASCAL_CASE,
                                                         TEST_NAME_PASCAL_CASE),
        '${primaryResourceIdentifier}': 'ResourceId'
    }
    templates_path = os.path.join(pathlib.Path(__file__).parent.parent, 'src', 'templates')
    metadata_template_path = os.path.join(templates_path, 'metadata.json')
    role_template_path = os.path.join(templates_path, 'AutomationAssumeRoleTemplate.yml')

    input_for_test = [SERVICE_NAME, TEST_DOC_TYPE, TEST_NAME, DATE, DISPLAY_NAME, DESCRIPTION, RESOURCE_ID,
                      FAILURE_TYPE, RISK, 'yes', 'no', ALARM_PREFIX, ALARM_ID]
    input_for_test_synth_alarm = [SERVICE_NAME, TEST_DOC_TYPE, TEST_NAME, DATE, DISPLAY_NAME, DESCRIPTION,
                                  RESOURCE_ID, FAILURE_TYPE, RISK, 'yes', 'yes', ALARM_PREFIX, ALARM_ID]
    input_for_test_no_rollback = [SERVICE_NAME, TEST_DOC_TYPE, TEST_NAME, DATE, DISPLAY_NAME, DESCRIPTION, RESOURCE_ID,
                                  FAILURE_TYPE, RISK, 'no', 'no', ALARM_PREFIX, ALARM_ID]
    input_for_sop = [SERVICE_NAME, SOP_DOC_TYPE, SOP_NAME, DATE, DISPLAY_NAME, DESCRIPTION, RESOURCE_ID, FAILURE_TYPE,
                     RISK, 'yes', RECOVERY_POINT_STEP]

    @patch('builtins.input', side_effect=[SERVICE_NAME, TEST_DOC_TYPE, TEST_NAME, DATE, 'no'])
    def test_no_overwrite(self, mock_inputs, mock_re, mock_open, mock_is_file, mock_mkdir, mock_is_dir):
        mock_is_dir.return_value = True
        mock_is_file.return_value = True
        with pytest.raises(SystemExit) as e:
            main()
        assert e.type == SystemExit
        assert e.value.code == 0
        mock_mkdir.assert_not_called()
        mock_re.assert_not_called()
        mock_open.assert_not_called()

    @patch('builtins.input', side_effect=input_for_test)
    def test_generate_test_with_recommended_alarm(self, mock_inputs, mock_re, mock_open, mock_is_file,
                                                  mock_mkdir, mock_is_dir):
        expected_replacements = {}
        expected_replacements.update(self.expected_replacements_common)
        expected_replacements['${alarmPrefix}'] = self.ALARM_PREFIX
        expected_replacements['${recommendedAlarms}'] = ',\n  "recommendedAlarms": {{ "{}AlarmName": "{}" }}'\
            .format(self.ALARM_PREFIX, self.ALARM_ID)
        self.__generate_and_validate(mock_re, mock_open, mock_is_file, mock_mkdir, mock_is_dir,
                                     expected_replacements, 'AutomationDocumentForTest.yml')

    @patch('builtins.input', side_effect=input_for_test_synth_alarm)
    def test_generate_test_synth_alarm(self, mock_inputs, mock_re, mock_open, mock_is_file, mock_mkdir, mock_is_dir):
        expected_replacements = {}
        expected_replacements.update(self.expected_replacements_common)
        expected_replacements['${alarmPrefix}'] = 'Synthetic'
        expected_replacements['${recommendedAlarms}'] = ''
        self.__generate_and_validate(mock_re, mock_open, mock_is_file, mock_mkdir, mock_is_dir,
                                     expected_replacements, 'AutomationDocumentForTest.yml')

    @patch('builtins.input', side_effect=input_for_test_no_rollback)
    def test_generate_test_no_rollback(self, mock_inputs, mock_re, mock_open, mock_is_file, mock_mkdir, mock_is_dir):
        expected_replacements = {}
        expected_replacements.update(self.expected_replacements_common)
        logging.info(expected_replacements)
        expected_replacements['${alarmPrefix}'] = self.ALARM_PREFIX
        expected_replacements['${recommendedAlarms}'] = ',\n  "recommendedAlarms": {{ "{}AlarmName": "{}" }}' \
            .format(self.ALARM_PREFIX, self.ALARM_ID)
        self.__generate_and_validate(mock_re, mock_open, mock_is_file, mock_mkdir, mock_is_dir,
                                     expected_replacements, 'AutomationDocumentForTestNoRollback.yml')

    @patch('builtins.input', side_effect=input_for_sop)
    def test_generate_sop(self, mock_inputs, mock_re, mock_open, mock_is_file, mock_mkdir, mock_is_dir):
        expected_replacements = {}
        expected_replacements.update(self.expected_replacements_common)
        expected_replacements['${recoveryPointStep}'] = '- name: {} # step that calculates the recovery point'\
            .format(self.RECOVERY_POINT_STEP)
        expected_replacements['${recoveryPointOutput}'] = '- {}.RecoveryPoint'.format(self.RECOVERY_POINT_STEP)
        expected_replacements['${recommendedAlarms}'] = ''
        self.__generate_and_validate(mock_re, mock_open, mock_is_file, mock_mkdir, mock_is_dir,
                                     expected_replacements, 'AutomationDocumentForSop.yml')

    def __generate_and_validate(self, mock_re, mock_open, mock_is_file, mock_mkdir, mock_is_dir,
                                expected_replacements: dict, automation_template: str):
        mock_is_dir.return_value = False
        mock_is_file.return_value = False
        main()
        mock_mkdir.assert_called_once()
        mock_re.escape.assert_has_calls([call(k) for k in expected_replacements.keys()], any_order=True)
        mock_open.assert_has_calls([call(self.metadata_template_path, 'r'), call(self.role_template_path, 'r'),
                                    call(os.path.join(self.templates_path, automation_template), 'r')],
                                   any_order=True)
