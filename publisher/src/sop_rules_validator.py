from publisher.src.rules_validator import RulesValidator
from publisher.src.rule import Rule
import publisher.src.ssm_automation_doc_rules as ssm_doc_rules


class RulesValidatorForSopDocument(RulesValidator):

    def __init__(self):
        RulesValidator.__init__(self, Rule(
            ssm_doc_rules.required_top_level_elements + ['outputs'],
            ssm_doc_rules.required_parameters,
            ssm_doc_rules.required_outputs + ['.*RecoveryTime'],
            ssm_doc_rules.required_steps + [['RecordStartTime'], ['OutputRecoveryTime']]
        ))

    def _validate_custom_rules(self, document, file_path, violations):
        pass
