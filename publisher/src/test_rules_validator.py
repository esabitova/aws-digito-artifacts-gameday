from publisher.src.rules_validator import RulesValidator
from publisher.src.rule import Rule
from publisher.src.parameter import Parameter
import publisher.src.ssm_automation_doc_rules as ssm_doc_rules


class TestRulesValidator(RulesValidator):
    is_rollback_param = Parameter('IsRollback', 'String', False)
    previous_exec_id_param = Parameter('PreviousExecutionId', 'String', False)
    alarm_red_steps = ['AssertAlarmTriggered', 'AssertAlarmToBeRed']
    rollback_branch_steps = ['CheckIsRollback', 'SelectExecutionMode']

    def __init__(self):
        RulesValidator.__init__(self, Rule(
            ssm_doc_rules.required_top_level_elements,
            ssm_doc_rules.required_parameters + [Parameter('.*AlarmName', 'String', True)],
            ssm_doc_rules.required_outputs,
            ssm_doc_rules.required_steps + [['AssertAlarmToBeGreenBeforeTest'],
                                            self.alarm_red_steps,
                                            ['AssertAlarmToBeGreen']]))

    def _validate_custom_rules(self, document, file_path, violations):
        self.__validate_rollback(document, file_path, violations)
        self.__validate_on_failure(document, file_path, violations)

    def __validate_rollback(self, document, file_path, violations):
        parameters = document.get('parameters')
        is_rollback_param_present = self._is_present(self.is_rollback_param.name, parameters)
        previous_exec_id_present = self._is_present(self.previous_exec_id_param.name, parameters)
        if (is_rollback_param_present and not previous_exec_id_present) or \
                (not is_rollback_param_present and previous_exec_id_present):
            violations.append('Either none or both of [{}], [{}] parameters should exist in [{}]'
                              .format(self.is_rollback_param.name, self.previous_exec_id_param.name, file_path))
        if is_rollback_param_present and \
                not self._is_step_present(self._get_step_names(document), self.rollback_branch_steps):
            violations.append('Missing steps [{}] in [{}]'.format(self.rollback_branch_steps, file_path))
        if is_rollback_param_present:
            document_steps = self._get_step_names(document)
            if not self._is_step_present(document_steps, self.rollback_branch_steps):
                violations.append('Missing steps [{}] in [{}]'.format(self.rollback_branch_steps, file_path))
            assert_step_names = list(map(lambda p: 'Assert' + p, parameters))
            if not self._is_step_present(document_steps, assert_step_names):
                violations.append('Missing step to validate equality of parameter value (of relevant parameters) '
                                  'with that of previous execution in [{}]'.format(file_path))

    def __validate_on_failure(self, document, file_path, violations):
        is_rollback_param_present = self._is_present(self.is_rollback_param.name, document.get('parameters'))
        if not is_rollback_param_present:
            return

        alarm_red_steps = self._get_steps(document, self.alarm_red_steps)
        if alarm_red_steps:
            alarm_red_step = alarm_red_steps[0]
            if not alarm_red_step.get('onFailure'):
                violations.append('Missing onFailure attribute for step [{}] in [{}]'
                                  .format(alarm_red_step.get('name'), file_path))
            elif alarm_red_step.get('onFailure') == 'Abort':
                violations.append('OnFailure attribute for step [{}] should be a valid step and not Abort in [{}]'
                                  .format(alarm_red_step.get('name'), file_path))
