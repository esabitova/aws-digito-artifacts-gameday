from publisher.src.test_rules_validator import TestRulesValidator
from publisher.src.sop_rules_validator import SopRulesValidator


class DocumentValidator:
    test_rules_validator = TestRulesValidator()
    sop_rules_validator = SopRulesValidator()

    def validate_document(self, document, file_path):
        failure_messages = []
        if '/test/' in file_path:
            failure_messages.extend(DocumentValidator.test_rules_validator.validate_document_rules(document, file_path))
        elif '/sop/' in file_path:
            failure_messages.extend(DocumentValidator.sop_rules_validator.validate_document_rules(document, file_path))
        return failure_messages
