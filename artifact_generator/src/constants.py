import pathlib
import os

FILE_PATH = pathlib.Path(__file__)
PACKAGE_DIR = FILE_PATH.parent.parent.parent.absolute()
TEMPLATES_DIR = os.path.join(FILE_PATH.parent.absolute(), 'templates')
AUTOMATION_DOC_NAME = 'AutomationDocument.yml'
ROLE_DOC_NAME = 'AutomationAssumeRoleTemplate.yml'
METADATA_DOC_NAME = 'metadata.json'
RISKS = ['SMALL', 'MEDIUM', 'HIGH']
FAILURE_TYPES = ['REGION', 'AZ', 'HARDWARE', 'SOFTWARE']
