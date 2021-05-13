import datetime
import os
import pathlib
import re
from artifact_generator.src.input_validator import InputValidator as validator

AUTOMATION_DOC_NAME = 'AutomationDocument.yml'
ROLE_DOC_NAME = 'AutomationAssumeRoleTemplate.yml'
METADATA_DOC_NAME = 'metadata.json'
SYNTHETIC_ALARM_PREFIX = 'Synthetic'
RISKS = ['SMALL', 'MEDIUM', 'HIGH']
FAILURE_TYPES = ['REGION', 'AZ', 'HARDWARE', 'SOFTWARE']


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
    date = input('Enter date in YYYY-MM-DD format if in the past, else we default to current date: \n')
    if not date.strip():
        date = datetime.date.today().strftime("%Y-%m-%d")
    else:
        validator.validate_date_input(date)
    return date


def __create_dir_if_not_exists(dir_path: str):
    """
    Creates directory if it does not exist
    :param dir_path: directory path
    """
    if not os.path.isdir(dir_path):
        print('Creating target folder path [{}]'.format(dir_path))
        os.makedirs(dir_path)


def __add_replacements_for_test(replacements: dict):
    """
    Get inputs specific to generating artifacts for test and add values to the replacement dictionary.
    :param replacements: dictionary that contains replacement value corresponding to placeholders in artifact templates
    """
    recommended_alarms = ''
    supports_synth_alarm = validator.validate_boolean_inputs(input('Does test support synthetic alarm (yes/no)?\n'))
    if supports_synth_alarm == 'no':
        alarm_prefix = validator.validate_alpha(input('Enter alarm name prefix - this will appear in the automation '
                                                      'input as <Prefix>AlarmName (ex: CpuUtilizationAlarmName\n'))
        alarm_id = input('Enter ID for recommended alarm (ex - compute:alarm:asg-cpu-util:2020-07-13)\n')
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
    supports_recovery_point = validator.validate_boolean_inputs(input('Does sop calculate recovery point (yes/no)?\n'))
    recovery_point_output = recovery_point_step = ''
    if supports_recovery_point == 'yes':
        recovery_point_step_name = validator.validate_alpha(input('Enter the name of the automation document step that '
                                                                  'calculates recovery point (ex: GetRecoveryPoint)\n'))
        recovery_point_output = '- {}.RecoveryPoint'.format(recovery_point_step_name)
        recovery_point_step = '- name: {} # step that calculates the recovery point'.format(recovery_point_step_name)
    replacements["${recoveryPointStep}"] = recovery_point_step
    replacements["${recoveryPointOutput}"] = recovery_point_output
    replacements["${recommendedAlarms}"] = ''


def __replace(source_file_path: str, target_file_path: str, replacements: dict):
    """
    Creates target artifact by replacing the placeholders in the source template.
    :param source_file_path: source file
    :param target_file_path: target file
    :param replacements: dictionary that contains replacement value corresponding to placeholders in artifact templates
    """
    source_file = open(source_file_path, "r")
    source_content = source_file.read()
    target_content = source_content
    for k, v in replacements.items():
        target_content = re.sub(re.escape(k), v, target_content)
    target_file = open(target_file_path, "w")
    target_file.write(target_content)
    source_file.close()
    target_file.close()


def main():
    service_name = validator.validate_small_case_with_hyphens(input('Enter service name (ex - api-gw):\n'))
    doc_type = validator.validate_input(input('Is this a test or a sop (test/sop)?: \n'), 'test|sop')
    name = validator.validate_small_case_with_underscore(input('Enter {} name (ex - restore_from_backup):\n'
                                                               .format(doc_type)))
    date = __get_date()

    file_path = pathlib.Path(__file__)
    main_docs_path = os.path.join(file_path.parent.parent.parent.absolute(), 'documents', service_name, doc_type, name,
                                  date, 'Documents')
    __create_dir_if_not_exists(main_docs_path)
    automation_doc_path = os.path.join(main_docs_path, AUTOMATION_DOC_NAME)
    role_doc_path = os.path.join(main_docs_path, ROLE_DOC_NAME)
    metadata_path = os.path.join(main_docs_path, METADATA_DOC_NAME)
    if __is_exists(automation_doc_path) or __is_exists(role_doc_path) or __is_exists(metadata_path):
        overwrite_files = validator.validate_boolean_inputs(
            input('One or more of {}, {}, {} already exists under {}. Do you want to overwrite them (yes/no)?'
                  .format(AUTOMATION_DOC_NAME, ROLE_DOC_NAME, METADATA_DOC_NAME, main_docs_path)))
        if overwrite_files == 'no':
            print('Nothing to do. Exiting.')
            exit(0)

    display_name = input('Enter display name:\n')
    description = input('Enter description:\n')
    resource_id = validator.validate_alpha(input('Enter a name for the primary resource ID input parameter '
                                                 '(ex: QueueUrl, DatabaseIdentifier):\n'))
    failure_type = validator.validate_one_or_more_of(input('Enter failure type(s) as a comma-separated list (one or '
                                                           'more of {}): \n'.format(','.join(FAILURE_TYPES))),
                                                     FAILURE_TYPES)
    risk = validator.validate_one_of(input('Enter risk ({}): \n'.format('/'.join(RISKS))), RISKS)

    replacements = {
        "${displayName}": display_name,
        "${description}": description,
        "${assumeRoleCfnPath}": ROLE_DOC_NAME,
        "${documentContentPath}": AUTOMATION_DOC_NAME,
        "${documentName}": "Digito-{}_{}".format(__pascal_case(name), date),
        "${failureType}": failure_type,
        "${risk}": risk,
        "${tag}": ":".join([service_name, doc_type, name, date]),
        "${roleName}": "Digito{}{}AssumeRole".format(__pascal_case(service_name), __pascal_case(name)),
        "${policyName}": "Digito{}{}AssumePolicy".format(__pascal_case(service_name), __pascal_case(name)),
        "${primaryResourceIdentifier}": resource_id
    }

    if doc_type == 'test':
        supports_rollback = validator.validate_boolean_inputs(input('Does test support rollback (yes/no)?\n'))
        __add_replacements_for_test(replacements)
        automation_doc_template = 'AutomationDocumentForTest.yml' if supports_rollback == 'yes'\
            else 'AutomationDocumentForTestNoRollback.yml'
    elif doc_type == 'sop':
        automation_doc_template = 'AutomationDocumentForSop.yml'
        __add_replacements_for_sop(replacements)

    templates_path = os.path.join(file_path.parent.absolute(), 'templates')
    print()
    print('Creating artifacts under [{}]'.format(main_docs_path))
    __replace(os.path.join(templates_path, METADATA_DOC_NAME), metadata_path, replacements)
    __replace(os.path.join(templates_path, ROLE_DOC_NAME), role_doc_path, replacements)
    __replace(os.path.join(templates_path, automation_doc_template), automation_doc_path, replacements)
    print('Successfully created artifacts. Please update them as required.')


if __name__ == '__main__':
    main()
