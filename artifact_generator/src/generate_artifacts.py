import datetime
import os
import re
from artifact_generator.src import constants
from artifact_generator.src.input_validator import InputValidator as validator
from typing import Callable

from artifact_generator.src.scenario_info import ScenarioInfo
from util.bg_colors import BgColors
from mako.lookup import TemplateLookup

USUAL_CASE_SOP_DOC_NAME = 'usual_case_sop.feature'
USUAL_CASE_TEST_DOC_NAME = 'usual_case_test.feature'
FAILED_DOC_TEST_NAME = 'failed.feature'
ROLLBACK_TEST_DOC_NAME = 'rollback_previous.feature'
SYNTHETIC_ALARM_PREFIX = 'Synthetic'
SCENARIO_PREFIX = 'Scenario:'
RISKS = ['SMALL', 'MEDIUM', 'HIGH']
FAILURE_TYPES = ['REGION', 'AZ', 'HARDWARE', 'SOFTWARE']
CFN_TEMPLATES_PATH = os.path.join(constants.PACKAGE_DIR, "resource_manager", "cloud_formation_templates")

template_lookup = TemplateLookup(constants.TEMPLATES_DIR)


def __is_exists(path: str):
    """
    Check if file exists
    :param path: Full path of file
    :return: true if file exists, false otherwise
    """
    return os.path.isfile(path)


def __pascal_case(text: str):
    """
    Converts string separated by hyphens or underscores to Pascal case. For example, api-gw or api_gw to ApiGw
    :param text: input text
    :return: text converted to Pascal case
    """
    return text.replace("-", " ").replace("_", " ").title().replace(" ", "")


def __get_date():
    """
    Get input date and validates that it is in the YYYY-MM-DD format. If no input is provided, defaults to the current
    date.
    :return: date
    """
    date = __get_input('Enter date in YYYY-MM-DD format if in the past, else we default to current date: \n')
    if not date.strip():
        date = datetime.date.today().strftime("%Y-%m-%d")
        print('Ok, using default value of {} for date\n'.format(date))
    else:
        validator.validate_date_input(date)
    return date


def __create_dir_if_not_exists(dir_path: str):
    """
    Creates directory if it does not exist
    :param dir_path: directory path
    """
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path)
        __print_success('Created target folder structure [{}]'.format(os.path.relpath(dir_path, constants.PACKAGE_DIR)))


def __add_replacements_for_test(replacements: dict):
    """
    Get inputs specific to generating artifacts for test and add values to the replacement dictionary.
    :param replacements: dictionary that contains replacement value corresponding to placeholders in artifact templates
    """
    recommended_alarms = ''
    supports_synth_alarm = __get_input('Does test support synthetic alarm (yes/no)?\n',
                                       validator.validate_boolean_inputs)
    if supports_synth_alarm == 'no':
        alarm_prefix = __get_input('Enter alarm name prefix - this will appear in the automation input as '
                                   '<Prefix>AlarmName (ex: CpuUtilizationAlarmName)\n',
                                   validator.validate_alpha_numeric_input)
        alarm_id = __get_input('Enter ID for recommended alarm (ex - compute:alarm:asg-cpu-util:2020-07-13)\n')
        recommended_alarms = ',\n  "recommendedAlarms": {{ "{}AlarmName": "{}" }}'.format(alarm_prefix, alarm_id)
    else:
        alarm_prefix = SYNTHETIC_ALARM_PREFIX
    replacements["${alarmPrefix}"] = alarm_prefix
    replacements["${recommendedAlarms}"] = recommended_alarms


def __add_replacements_for_sop(replacements: dict):
    """
    Get inputs specific to generating artifacts for SOP and add values to the replacement dictionary.
    :param replacements: dictionary that contains replacement value corresponding to placeholders in artifact templates
    """
    supports_recovery_point = __get_input('Does sop calculate recovery point (yes/no)?\n',
                                          validator.validate_boolean_inputs)
    recovery_point_output = recovery_point_step = ''
    if supports_recovery_point == 'yes':
        recovery_point_step_name = __get_input('Enter name of the automation document step that calculates recovery '
                                               'point (ex: GetRecoveryPoint)\n', validator.validate_alpha)
        recovery_point_output = '- {}.RecoveryPoint'.format(recovery_point_step_name)
        recovery_point_step = '- name: {} # step that calculates the recovery point'.format(recovery_point_step_name)
    replacements["${recoveryPointStep}"] = recovery_point_step
    replacements["${recoveryPointOutput}"] = recovery_point_output
    replacements["${recommendedAlarms}"] = ''


def __create_artifact(source_template_path: str, target_file_path: str, replacements: dict):
    """
    Creates target artifact by replacing the placeholders in the source template.
    :param source_template_path: source template file
    :param target_file_path: target file
    :param replacements: dictionary that contains replacement value corresponding to placeholders in artifact templates
    """
    with open(source_template_path, "r") as source_file:
        source_content = source_file.read()
        target_content = source_content
        for k, v in replacements.items():
            target_content = re.sub(re.escape(k), v, target_content)
        with open(target_file_path, "w") as target_file:
            target_file.write(target_content)


def ___exit_if_exists_and_no_overwrite(files: list):
    """
    Checks if any one of the specified files exist and if yes, checks if the files should be overwritten. If the user
    chooses not to overwrite, the script is exited.
    :param files: list of files to check existence for
    """
    if any([__is_exists(file) for file in files]):
        file_names = [os.path.basename(f) for f in files]
        overwrite_files = __get_input('One or more of {} already exists. Do you want to overwrite them (yes/no)?\n'
                                      .format(",".join(file_names)), validator.validate_boolean_inputs)
        if overwrite_files == 'no':
            print('Nothing to do. Exiting.')
            exit(0)


def __get_cfn_template_info(doc_name: str, doc_type: str, resource_id: str, replacements: dict):
    """
    Get information about the cloudFormation template as inputs.
    :param doc_name: SSM document name
    :param doc_type: test or sop document
    :param resource_id: primary resource identifier input of the SSM document
    :param replacements: dictionary that contains replacement value corresponding to placeholders in artifact templates
    :return:
    """
    print('\nWe use cloudformation templates to create the resources for testing test/SOP documents. '
          'These are located under {}.\n\n'.format(os.path.relpath(CFN_TEMPLATES_PATH, constants.PACKAGE_DIR)))

    cfn_template_name = __get_input('Enter the name of the cloudformation template for testing {} '
                                    '(ex: SqsTemplate, RdsTemplate):\n'.format(doc_name),
                                    validator.validate_alpha_numeric_input)
    replacements['${cfnTemplateName}'] = cfn_template_name

    cfn_resource_id_output = __get_input('Enter the name of the cloudformation output for {}\n'
                                         .format(resource_id), validator.validate_alpha_numeric_input)
    replacements['${resourceIdOutput}'] = cfn_resource_id_output

    alarm_name_output = ''
    if doc_type == 'test':
        cfn_alarm_id_output = __get_input('Enter the name of the cloudformation output for {}AlarmName\n'
                                          .format(replacements['${alarmPrefix}']),
                                          validator.validate_alpha_numeric_input)
        alarm_name_output = cfn_alarm_id_output
    replacements['${alarmNameOutput}'] = alarm_name_output

    cfn_absolute_path = os.path.join(CFN_TEMPLATES_PATH, cfn_template_name + '.yml')
    if not __is_exists(cfn_absolute_path):
        create_cfn = __get_input('There is no {} under {}. Would you like artifact generator to create one (yes/no)?\n'
                                 .format(cfn_template_name, os.path.relpath(CFN_TEMPLATES_PATH, constants.PACKAGE_DIR)),
                                 validator.validate_boolean_inputs)
        if create_cfn == 'yes':
            __create_artifact(os.path.join(constants.TEMPLATES_DIR, "CloudFormationTemplate.yml"), cfn_absolute_path,
                              replacements)
            __print_success('Created {}'.format(os.path.relpath(cfn_absolute_path, constants.PACKAGE_DIR)))
        else:
            required_outputs = ','.join([cfn_resource_id_output, alarm_name_output if alarm_name_output else ''])
            print('Okay. Proceeding without creating the cloudformation template. Please make sure you create {} with '
                  'output(s) {} in order for the integration tests to work'.format(cfn_template_name,
                                                                                   required_outputs))


def __get_feature_file_templates_applicable(doc_type: str, supports_rollback: str):
    """
    Get the feature file templates applicable to the automation document
    :param doc_type: test or sop
    :param supports_rollback: whether or not the document supports rollback
    :return: list of feature file templates applicable to the automation document
    """
    feature_file_templates = []
    if doc_type == 'test':
        feature_file_templates.append(USUAL_CASE_TEST_DOC_NAME)
        if supports_rollback == 'yes':
            feature_file_templates.extend([ROLLBACK_TEST_DOC_NAME, FAILED_DOC_TEST_NAME])
    elif doc_type == 'sop':
        feature_file_templates.append(USUAL_CASE_SOP_DOC_NAME)
    return feature_file_templates


def __get_scenarios(feature_files: str, step_def_location: str):
    """
    Parses the input feature files to get scenario information
    :param feature_files: list of feature files
    :param step_def_location: path to the step_defs directory
    :return: scenario information
    """
    scenarios = []
    for file in feature_files:
        with open(file, "r") as f:
            for ln in f:
                if ln.strip().startswith(SCENARIO_PREFIX):
                    scenarios.append(ScenarioInfo(ln.strip()[len(SCENARIO_PREFIX):].strip(),
                                                  os.path.relpath(file, step_def_location)))
    return scenarios


def __create_role_doc(target_file_path: str, doc_name: str, service_name: str, name: str,
                      supports_rollback: str, role_name: str):
    policy_name = "Digito{}{}AssumePolicy".format(__pascal_case(service_name), __pascal_case(name))
    role_content = template_lookup.get_template('AutomationAssumeRoleTemplate.yml.mak')\
        .render(documentName=doc_name, roleName=role_name, policyName=policy_name, supportsRollback=supports_rollback)
    with open(target_file_path, "w") as f:
        f.write(role_content)


def __create_feature_files(name: str, doc_name: str, doc_type: str, res_id: str,
                           test_location: str, replacements: list, supports_rollback: str):
    """
    Create the feature files for the test/sop in the specified target path
    :param name: test/sop name
    :param doc_name: SSM document name
    :param doc_type: test or sop document
    :param res_id: primary resource identifier input of the SSM document
    :param test_location: target Tests directory location
    :param replacements: dictionary that contains replacement value corresponding to placeholders in artifact templates
    :param supports_rollback: whether or not the document supports rollback
    :return:
    """
    feature_templates = __get_feature_file_templates_applicable(doc_type, supports_rollback)
    test_features_location = os.path.join(test_location, 'features')
    template_targets = {}
    for t in feature_templates:
        template_targets[t] = os.path.join(test_features_location, '{}_{}'.format(name, re.sub('_test|_sop', '', t)))

    ___exit_if_exists_and_no_overwrite(template_targets.values())
    __get_cfn_template_info(doc_name, doc_type, res_id, replacements)
    __create_dir_if_not_exists(test_features_location)

    for template, target in template_targets.items():
        __create_artifact(os.path.join(constants.TEMPLATES_DIR, template), target, replacements)
    return template_targets.values()


def __get_input(prompt: str, validate: Callable = None, validate_args=None, max_attempts: int = 2):
    """
    Get input upto specified maximum number of attempts in case of validation error.
    :param prompt: input prompt
    :param validate: validation method used to validate the input value
    :param validate_args: any additional argument required by the validate method
    :param max_attempts: maximum number of attempts made to get input (including the first attempt) in case of error
    :return:
    """
    for attempt in range(0, max_attempts):
        try:
            value = input(BgColors.OKBLUE + prompt + BgColors.ENDC)
            if not validate:
                return value
            if validate_args:
                return validate(value, validate_args)
            else:
                return validate(value)
        except ValueError as e:
            if attempt < max_attempts - 1:
                print(BgColors.FAIL + str(e) + BgColors.ENDC, end=" ")
            else:
                raise e


def __print_header(prompt: str):
    """
    Syntax for printing headers
    :param prompt: prompt
    """
    print(BgColors.BOLD + BgColors.HEADER + prompt + BgColors.ENDC + '\n')


def __print_success(prompt: str):
    """
    Syntax for printing success message
    :param prompt: prompt
    """
    print(BgColors.OKGREEN + prompt + BgColors.ENDC + '\n')


def main():
    __print_header('------------------------------------------------------------\n'
                   '-------------- Welcome to Artifact Generator ---------------\n'
                   '------------------------------------------------------------\n')
    print('Artifact generator will help you get started by creating \n'
          'outlines of documents required for your test/SOP. You can\n'
          'then update these documents as per your requirement.\n'
          'Let\'s get started!\n')

    service_name = __get_input('Enter service name(ex - api-gw):\n', validator.validate_small_case_numeric_with_hyphens)
    doc_type = __get_input('Is this a test or a sop (test/sop)?: \n', validator.validate_input, 'test|sop')
    name = __get_input('Enter {} name (ex - restore_from_backup):\n'.format(doc_type),
                       validator.validate_small_case_with_underscore)
    date = __get_date()

    artifacts_dir = os.path.join(constants.PACKAGE_DIR, 'documents', service_name, doc_type, name, date)

    __print_header('Step 1: Create artifacts under Documents folder\n')
    main_docs_path = os.path.join(constants.PACKAGE_DIR, artifacts_dir, 'Documents')

    automation_doc_path = os.path.join(main_docs_path, constants.AUTOMATION_DOC_NAME)
    role_doc_path = os.path.join(main_docs_path, constants.ROLE_DOC_NAME)
    metadata_path = os.path.join(main_docs_path, constants.METADATA_DOC_NAME)
    ___exit_if_exists_and_no_overwrite([automation_doc_path, role_doc_path, metadata_path])

    display_name = __get_input('Enter display name:\n')
    description = __get_input('Enter description:\n')
    resource_id = __get_input('Enter a name for the primary resource ID input parameter '
                              '(ex: QueueUrl, DatabaseIdentifier):\n', validator.validate_alpha_numeric_input)
    failure_type = __get_input('Enter failure type(s) as a comma-separated list (one or '
                               'more of {}): \n'.format(','.join(FAILURE_TYPES)),
                               validator.validate_one_or_more_of, FAILURE_TYPES)
    risk = __get_input('Enter risk ({}): \n'.format('/'.join(RISKS)), validator.validate_one_of, RISKS)

    document_name = "Digito-{}_{}".format(__pascal_case(name), date)
    role_name = "Digito{}{}AssumeRole".format(__pascal_case(service_name), __pascal_case(name))
    replacements = {
        "${serviceName}": service_name,
        "${documentType}": doc_type,
        "${name}": name,
        "${date}": date,
        "${displayName}": display_name,
        "${description}": description,
        "${assumeRoleCfnPath}": constants.ROLE_DOC_NAME,
        "${documentContentPath}": constants.AUTOMATION_DOC_NAME,
        "${documentName}": document_name,
        "${failureType}": failure_type,
        "${risk}": risk,
        "${tag}": ":".join([service_name, doc_type, name, date]),
        "${roleName}": role_name,
        "${policyName}": "Digito{}{}AssumePolicy".format(__pascal_case(service_name), __pascal_case(name)),
        "${primaryResourceIdentifier}": resource_id
    }

    supports_rollback = 'no'
    if doc_type == 'test':
        supports_rollback = __get_input('Does test support rollback (yes/no)?\n', validator.validate_boolean_inputs)
        __add_replacements_for_test(replacements)
        automation_doc_template = 'AutomationDocumentForTest.yml' if supports_rollback == 'yes' \
            else 'AutomationDocumentForTestNoRollback.yml'
    elif doc_type == 'sop':
        automation_doc_template = 'AutomationDocumentForSop.yml'
        __add_replacements_for_sop(replacements)

    print()
    __create_dir_if_not_exists(main_docs_path)
    __create_artifact(os.path.join(constants.TEMPLATES_DIR, constants.METADATA_DOC_NAME), metadata_path, replacements)
    __create_role_doc(role_doc_path, doc_name=document_name, service_name=service_name, name=name,
                      supports_rollback=supports_rollback, role_name=role_name)
    __create_artifact(os.path.join(constants.TEMPLATES_DIR, automation_doc_template), automation_doc_path, replacements)
    __print_success('Successfully created artifacts under {}.'.format(os.path.relpath(main_docs_path,
                                                                                      constants.PACKAGE_DIR)))

    __print_header('Step 2: Create tests under Tests folder\n')
    test_location = os.path.join(artifacts_dir, 'Tests')
    feature_files = __create_feature_files(name=name, doc_name=document_name, doc_type=doc_type,
                                           res_id=resource_id, test_location=test_location, replacements=replacements,
                                           supports_rollback=supports_rollback)
    # create scenario test code
    step_def_location = os.path.join(test_location, 'step_defs')
    step_def_file = os.path.join(step_def_location, 'test_{}.py'.format(name.replace('-', '_')))
    ___exit_if_exists_and_no_overwrite([step_def_file])
    step_def_content = template_lookup.get_template("step_def.py.mak").render(
        scenarios=__get_scenarios(feature_files, step_def_location),
        get_test_suffix=lambda path: os.path.split(path)[1].split(".")[0])
    __create_dir_if_not_exists(step_def_location)
    with open(step_def_file, "w") as f:
        f.write(step_def_content)

    __print_success('Successfully created artifacts under {}.'.format(os.path.relpath(test_location,
                                                                                      constants.PACKAGE_DIR)))
    __print_header('Artifact generator has finished creating all documents. Please update them as required.')


if __name__ == '__main__':
    main()
