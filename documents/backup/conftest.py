import logging

from pytest_bdd import (
    then,
    parsers
)

from resource_manager.src.util.efs_utils import describe_filesystem
from resource_manager.src.util.backup_utils import issue_a_backup_job_and_immediately_abort_it
from resource_manager.src.util.common_test_utils import extract_param_value


logger = logging.getLogger(__name__)


@then(parsers.parse('issue a backup job for FileSystemId in '
                    'BackupVaultDestinationName and immediately abort it\n{input_parameters}'))
def issue_a_backup_job_for_efs_and_abort_it(resource_pool, boto3_session, ssm_test_cache, input_parameters):
    efs_id = extract_param_value(input_parameters, 'FileSystemId', resource_pool, ssm_test_cache)
    efs_arn = describe_filesystem(boto3_session, efs_id)['FileSystems'][0]['FileSystemArn']
    iam_role_arn = extract_param_value(input_parameters, 'BackupJobIamRoleArn', resource_pool, ssm_test_cache)
    backup_vault_name = extract_param_value(input_parameters,
                                            'BackupVaultDestinationName',
                                            resource_pool,
                                            ssm_test_cache
                                            )

    issue_a_backup_job_and_immediately_abort_it(boto3_session,
                                                efs_arn,
                                                iam_role_arn,
                                                backup_vault_name
                                                )
