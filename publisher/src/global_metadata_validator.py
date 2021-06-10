import re
from collections import defaultdict


class GlobalMetadataValidator:
    attrs_map = defaultdict(set)
    unique_attributes = ['tag']
    unique_cfn_attributes = ['alarmName', 'documentName']

    def iterate_file(self, metadata_content, filepath):
        self._register_unique_attributes(metadata_content, filepath)
        self._register_unique_cfn_attributes(metadata_content, filepath)

    def get_metadata_violations(self):
        violations = []
        self._validate_unique_values(violations)
        return violations

    def _register_unique_attributes(self, metadata_content, filepath):
        for attribute in self.unique_attributes:
            if attribute in metadata_content:
                self.attrs_map[(attribute, metadata_content[attribute])].add(filepath)

    def _register_unique_cfn_attributes(self, metadata_content, filepath):
        for attribute in self.unique_cfn_attributes:
            if attribute in metadata_content:
                self.attrs_map[(f'cfn-{attribute}', self._cfn_resource_name(metadata_content[attribute]))].add(filepath)

    def _validate_unique_values(self, violations):
        for (type, value), files in self.attrs_map.items():
            if len(files) > 1:
                violations.append(f"Found non-unique {type} for {value} in files: {files}")

    def _cfn_resource_name(self, str):
        return re.sub(r"[^a-zA-Z0-9]", "", str)
