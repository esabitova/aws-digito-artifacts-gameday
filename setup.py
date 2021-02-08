import os
import json
from setuptools import setup

SCRIPT_DIR = '/documents/util/scripts/src/'
SCRIPT_ZIP_FILE_NAME = 'digito_gameday_primitives.zip'
AUTOMATION_DOCUMENT_FINAL_NAME = 'AutomationDocumentFinal.yml'
ROOT_DIR = os.getcwd()

# Adding data files documents, artifacts under build folder.
data_files = []
for root, dirs, files in os.walk("documents"):
    if "alarm" in dirs:
        dirs.remove("alarm")

    for f in files:
        data_files.append((root, [os.path.join(root, f)]))

        if f == "metadata.json":
            automation_document_content_final = ""
            with open(os.path.join(root, f)) as metadata_file:
                document_metadata = json.load(metadata_file)
                with open(os.path.join(root, document_metadata['documentContentPath']), 'r') as automation_document:
                    automation_document_content_lines = automation_document.read().splitlines()
                    for automation_document_content_line in automation_document_content_lines:
                        if "SCRIPT_PLACEHOLDER" in automation_document_content_line:
                            script_placeholder = automation_document_content_line.strip()
                            script_file_name = script_placeholder.split("::")[1].split(".")[0]
                            script_method_name = script_placeholder.split("::")[1].split(".")[1]

                            script_lines = []
                            script_lines_to_be_included = ""
                            with open(ROOT_DIR + SCRIPT_DIR + script_file_name + '.py') as f:
                                script_lines = f.read().splitlines()

                                is_first_line = True
                                before_first_method = True
                                found_method = False

                                for line in script_lines:
                                    if before_first_method and "def " in line:
                                        before_first_method = False

                                    # found another method, break
                                    if found_method and ("def " in line):
                                        break

                                    if "def " + script_method_name + "(" in line:
                                        found_method = True

                                    # Add all lines before first method if it is imports
                                    # part of the method in script_placeholder
                                    if (before_first_method and script_method_name == "imports") or found_method:
                                        # Add 8 spaces to all lines except first line so that it
                                        # aligns with ssm document yaml format
                                        if (is_first_line):
                                            is_first_line = False
                                        else:
                                            line = "        " + line
                                        script_lines_to_be_included += line + "\n"

                            script_content = script_lines_to_be_included
                            automation_document_content_line = automation_document_content_line\
                                .replace(script_placeholder, script_content)

                        automation_document_content_final += automation_document_content_line + "\n"
                    with open(os.path.join(root, AUTOMATION_DOCUMENT_FINAL_NAME), 'w') as automation_document_output:
                        automation_document_output.write(automation_document_content_final)
                    data_files.append((root, [os.path.join(root, AUTOMATION_DOCUMENT_FINAL_NAME)]))

setup(
    name="AwsDigitoArtifactsGameday",
    version="1.0",
    # Use the pytest brazilpython runner. Provided by BrazilPython-Pytest.
    test_command="brazilpython_pytest",
    # include data files
    data_files=data_files,
    root_script_source_version='python3.7',
    # Enable build-time format checking
    check_format=True,
    # Enable linting at build time
    test_flake8=True
)
