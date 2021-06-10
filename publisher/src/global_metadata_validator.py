import json
import os
import re


class GlobalMetadataValidator:
    unique_attributes = {}

    def __init__(self):
        pass

    def get_metadata_violations(self, root, files):
        violations = []
        self._validate_unique_tag(root, files, violations)
        return violations

    def _validate_unique_tag(self, root, files, violations):
        for f in files:
            if f == 'metadata.json':
                with open(os.path.join(root, f)) as metadata_file:
                    metadata_content = json.load(metadata_file)
                    self._validate_unique_attribute(metadata_content, "tag", violations)
                    self._validate_unique_cfn_attribute(metadata_content, "alarmName", violations)
                    self._validate_unique_cfn_attribute(metadata_content, "documentName", violations)

    def _validate_unique_attribute(self, metadata_content, type, violations):
        if type not in metadata_content:
            return
        self._validate_unique_value(type, metadata_content[type], violations)

    def _validate_unique_cfn_attribute(self, metadata_content, type, violations):
        if type not in metadata_content:
            return
        self._validate_unique_value(f'cfn-{type}', self._cfn_resource_name(metadata_content[type]), violations)

    def _validate_unique_value(self, type, value, violations):
        if type not in self.unique_attributes:
            self.unique_attributes[type] = []
        if value in self.unique_attributes[type]:
            violations.append(f"Found non-unique {type}: {value}")
        self.unique_attributes[type].append(value)

    def _cfn_resource_name(self, str):
        return re.sub(r"[^a-zA-Z0-9]", "", str)
