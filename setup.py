import os
import zipfile
from setuptools import setup, find_packages

SCRIPT_DIR = '/documents/util/scripts/src'
SCRIPT_ZIP_FILE_NAME = 'digito_gameday_primitives.zip'
ROOT_DIR = os.getcwd()

# Zipping SSM automation document attachment.
with zipfile.ZipFile(SCRIPT_ZIP_FILE_NAME, 'w', zipfile.ZIP_DEFLATED) as zipfile_handle:
    for root, dirs, files in os.walk(ROOT_DIR + SCRIPT_DIR):
        os.chdir(root)
        for file in files:
            zipfile_handle.write(file)
    os.chdir(ROOT_DIR)

# Adding data files documents, artifacts under build folder.
data_files = []
for root, dirs, files in os.walk("documents"):
    data_files.append((root, [os.path.join(root, f) for f in files]))
data_files.append(('.', [SCRIPT_ZIP_FILE_NAME]))

setup(
    name="AwsDigitoArtifactsGameday",
    version="1.0",
    # Use the pytest brazilpython runner. Provided by BrazilPython-Pytest.

    # TODO (semiond): Temp workaround to trigger brazil build instead running tests, till following done:
    # https://issues.amazon.com/issues/Digito-1565
    # test_command="brazilpython_pytest",
    test_command="build",

    # include data files
    data_files=data_files,
    root_script_source_version='python3.7'
)
