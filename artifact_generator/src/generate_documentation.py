import os
import json
import logging
import pathlib
import sys
import yaml
from artifact_generator.src import constants
from cfn_tools import load_yaml
from mako.lookup import TemplateLookup

DOCS_DIR = 'documents/'
UTIL = 'util'
UTIL_DIR = DOCS_DIR + UTIL + '/'

template_lookup = TemplateLookup(constants.TEMPLATES_DIR)

logger = logging.getLogger('generate_documentation')
logging.basicConfig(format='%(asctime)s %(name)s %(levelname)s:%(message)s', level=logging.INFO,
                    handlers=[logging.StreamHandler(sys.stdout)])


class DocumentationInfo:
    """
    Class for storing documentation information
    """
    def __init__(self, id, type, metadata_doc_content, automation_doc_content, role_doc_content):
        self.permissions = []
        if role_doc_content:
            for k, v in role_doc_content['Resources'].items():
                if k.endswith("Policy"):
                    statements = (v['Properties']['PolicyDocument']['Statement'])
                    for s in statements:
                        if s['Effect'] == 'Allow':
                            self.permissions.extend(s['Action'])
        self.alarms = {}
        if 'recommendedAlarms' in metadata_doc_content:
            alarms = metadata_doc_content['recommendedAlarms']
            for k, v in alarms.items():
                self.alarms[k] = v
        self.depends_on = []
        if 'dependsOn' in metadata_doc_content:
            for dependency in metadata_doc_content['dependsOn'].split(','):
                self.depends_on.append(dependency)

        self.id = id
        self.doc_type = type
        self.ssm_doc_type = metadata_doc_content['documentType']
        # below are non-mandatory content so we use defaults
        # TODO add description, failure type and risk to util documents
        self.description = metadata_doc_content.get('description', '')
        self.failureType = metadata_doc_content.get('failureType', '')
        self.risk = metadata_doc_content.get('risk', '')
        self.inputs = automation_doc_content.get('parameters', None)
        self.outputs = automation_doc_content.get('outputs', None)
        self.is_rollback = 'Yes' if self.inputs and 'IsRollback' in self.inputs else 'No'

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


def __get_id_and_type(doc_path: str):
    """
    Get the id and type of test/sop/util based on the path to Documents directory
    :param doc_path: Documents directory path
    :return:  id anf type of the test/sop/util
    """
    start_path = UTIL_DIR if doc_path.startswith(UTIL_DIR) else DOCS_DIR
    components = os.path.dirname(doc_path[doc_path.find(start_path) + len(start_path):]).split('/')

    if doc_path.startswith(UTIL_DIR):
        type = 'util'
        id = ':'.join([components[0], type, components[1], components[2]])
    else:
        type = components[1]
        id = ':'.join(components)
    return id, type


def __generate_documentation(docs_dir: str):
    """
    Generate documentation for the test/sop/util
    :param docs_dir: Documents directory path
    """
    id, type = __get_id_and_type(docs_dir)

    with open(os.path.join(docs_dir, constants.METADATA_DOC_NAME), 'r') as f:
        metadata_content = json.load(f)
    with open(os.path.join(docs_dir, constants.AUTOMATION_DOC_NAME), 'r') as f:
        automation_content = yaml.safe_load(f)
    role_content = None
    if not docs_dir.startswith(UTIL_DIR):
        with open(os.path.join(docs_dir, constants.ROLE_DOC_NAME), 'r') as f:
            role_content = load_yaml(f)

    document_info = DocumentationInfo(id, type, metadata_content, automation_content, role_doc_content=role_content)
    target_content = template_lookup.get_template('Document.md.mak').render(doc_info=document_info)
    documentation_file = os.path.join(pathlib.Path(docs_dir).parent, 'Document.md')
    with open(documentation_file, 'w') as f:
        f.write(target_content)


def main():
    for root, dirs, files in os.walk(DOCS_DIR):
        if "not_completed" in dirs:
            dirs.remove('not_completed')
        for dir in dirs:
            # skip generation for tests/sops that have none of the documents (happens when we only have a spec).
            # If only some of the required documents is missing, then is is unexpected and should fail this script
            if dir == 'Documents':
                dir_path = os.path.join(root, dir)
                if dir_path.startswith(UTIL_DIR) or '/test/' in dir_path or '/sop/' in dir_path:
                    logging.info('Generating documentation for {}'.format(dir_path))
                    __generate_documentation(dir_path)
    logging.info('Successfully generated all documentation artifacts')


if __name__ == "__main__":
    main()
