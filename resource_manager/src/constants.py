# Number of seconds to wait for resources per waiting iteration
sleep_time_secs = 5
# Number of seconds to wait for resources before time out
wait_time_out_secs = 3600
# Cloud formation step completion wait time per iteration
cf_operation_sleep_time_secs = 20
# S3 bucket name patter for integration test cfn templates
s3_bucket_name_pattern = 'ssm-test-resources-<account_id>-<region_name>'
# TriggerRollback step constants
rollback_step_name = 'TriggerRollback'
rollback_execution_id_output_name = 'RollbackExecutionId'
