from publisher.src.test_rules_validator import RulesValidatorForTestDocument
from publisher.src.sop_rules_validator import RulesValidatorForSopDocument


class DocumentValidator:
    test_rules_validator = RulesValidatorForTestDocument()
    sop_rules_validator = RulesValidatorForSopDocument()

    def validate_document(self, document, file_path):
        failure_messages = []
        if '/test/' in file_path:
            failure_messages.extend(DocumentValidator.test_rules_validator.validate_document_rules(document, file_path))
        elif '/sop/' in file_path:
            failure_messages.extend(DocumentValidator.sop_rules_validator.validate_document_rules(document, file_path))
        return failure_messages
