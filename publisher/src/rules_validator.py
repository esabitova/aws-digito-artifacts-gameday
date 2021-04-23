import re
from abc import ABC, abstractmethod
from publisher.src.parameter import Parameter


class RulesValidator(ABC):
    def __init__(self, rule):
        self.rule = rule

    def validate_document_rules(self, document, file_path):
        violations = []

        self._validate_top_level_elements(document, file_path, violations)
        if violations:
            return violations

        self._validate_parameter_syntax(document, file_path, violations)
        self._validate_required_params(document, file_path, violations)
        self._validate_required_outputs(document, file_path, violations)
        self._validate_steps(document, file_path, violations)
        self._validate_custom_rules(document, file_path, violations)
        return violations

    def _validate_top_level_elements(self, document, file_path, violations):
        for element in self.rule.required_document_elements:
            if element not in document:
                violations.append('Required top-level element [{}] missing in [{}].'.format(element, file_path))

    def _validate_parameter_syntax(self, document, file_path, violations):
        parameters = document.get('parameters')
        for param in parameters:
            if not self._is_pascal_case(param):
                violations.append('Parameter [{}] should begin with a capital letter and follow camel casing in [{}].'
                                  .format(param, file_path))
            param_value = parameters.get(param)
            if 'description' not in param_value:
                violations.append('Description for [{}] parameter missing in [{}].'.format(param, file_path))
            else:
                description = param_value.get('description').strip()
                if not (description.startswith('(Required)') or description.startswith('(Optional)')):
                    violations.append(
                        'Description should start with \"(Required)\" or \"(Optional)\" for parameter [{}] in [{}].'
                        .format(param, file_path))
                if description.startswith('(Required)') and 'default' in param_value:
                    violations.append('Parameter [{}] has default value and must not be marked as Required in [{}].'
                                      .format(param, file_path))
                elif description.startswith('(Optional)') and 'default' not in param_value:
                    violations.append('Parameter [{}] has no default value and must not be marked as Optional in [{}].'
                                      .format(param, file_path))

            if 'type' not in param_value:
                violations.append('Parameter [{}] is missing a type in [{}].'.format(param, file_path))
            elif param_value.get("type") == 'SecureString':
                violations.append('Parameter [{}] uses disallowed type SecureString in [{}].'.format(param, file_path))

            if 'default' in param_value and str(param_value.get('default')).startswith('ssm:{{'):
                violations.append('Default value for parameter [{}] is trying to built on another parameter in [{}].'
                                  .format(param, file_path))

    def _validate_required_params(self, document, file_path, violations):
        document_params = document.get('parameters')
        for required_param in self.rule.required_parameters:
            matching_param = self._find_match(required_param.name, document_params)
            if not matching_param:
                violations.append('Parameter matching [{}] missing in [{}].'.format(required_param.name, file_path))
            else:
                matching_param = matching_param[0]
                self._assert_parameter_fields(matching_param, document_params.get(matching_param),
                                              required_param, file_path, violations)

    def _validate_required_outputs(self, document, file_path, violations):
        doc_outputs = document.get('outputs')
        for required_output in self.rule.required_outputs:
            if not self._is_present(required_output, doc_outputs):
                violations.append('Output matching [{}] missing in [{}].'.format(required_output, file_path))

    def _validate_steps(self, document, file_path, violations):
        doc_step_names = self._get_step_names(document)
        for steps in self.rule.required_steps:
            if not self._is_step_present(doc_step_names, steps):
                violations.append('Missing step [{}] in [{}]'.format(str(steps), file_path))

    @abstractmethod
    def _validate_custom_rules(self, document, file_path, violations):
        pass

    def _is_step_present(self, doc_step_names, target_step_names):
        for target_step_name in target_step_names:
            if self._is_present(target_step_name, doc_step_names):
                return True
        return False

    def _find_match(self, pattern, string_list):
        return [s for s in string_list if re.fullmatch(pattern, s) is not None]

    def _is_present(self, pattern, string_list):
        return len(self._find_match(pattern, string_list)) > 0

    def _is_pascal_case(self, s):
        return len(s) > 0 and s[0] == s[0].upper() and s != s.lower() and s != s.upper() and "_" not in s

    def _assert_parameter_fields(self, parameter_name, doc_parameter, expected_parameter: Parameter,
                                 file_path, violations):
        if doc_parameter.get('type') != expected_parameter.param_type:
            violations.append('Parameter [{}] should have type [{}] in [{}].'
                              .format(parameter_name, expected_parameter.param_type, file_path))
        if expected_parameter.required and doc_parameter.get('default') is not None:
            violations.append('Parameter [{}] should be required and not have a default in [{}].'
                              .format(parameter_name, file_path))
        elif not expected_parameter.required and not doc_parameter.get('default'):
            violations.append('Parameter [{}] should be optional and have a default in [{}].'
                              .format(parameter_name, file_path))

    def _get_step_names(self, document):
        return list(map(lambda s: s.get('name'), document.get('mainSteps')))

    def _get_steps(self, document, target_step_names):
        doc_steps = document.get('mainSteps')
        matching_steps = []
        for step in target_step_names:
            matching_steps.extend([s for s in doc_steps if re.fullmatch(step, s.get('name')) is not None])
        return matching_steps
