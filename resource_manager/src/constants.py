# Number of seconds to wait for resources per waiting iteration
sleep_time_secs = 5
# Number of seconds to wait for resources before time out
wait_time_out_secs = 7200
# Cloud formation step completion wait time per iteration
cf_operation_sleep_time_secs = 20
# S3 bucket name patter for integration test cfn templates
s3_bucket_name_pattern = 'ssm-test-resources-<account_id>-<region_name>'
# TriggerRollback step constants
rollback_step_name = 'TriggerRollback'
rollback_execution_id_output_name = 'RollbackExecutionId'


# Logging text output colors
class BgColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
