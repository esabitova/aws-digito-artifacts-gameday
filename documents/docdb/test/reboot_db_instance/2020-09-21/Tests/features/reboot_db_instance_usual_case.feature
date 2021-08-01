@docdb
Feature: SSM automation document Digito-RebootDbInstance_2020-09-21

  Scenario: Execute SSM automation document Digito-RebootDbInstance_2020-09-21
    Given the cached input parameters
      | DistributionPackageRelativePath                                                  | DistributionPackageS3Key         |
      | documents/docdb/canary/database-connection-canary/database-connection-canary.zip | canary/database-alarm-canary.zip |
    #todo DIG-977 create CW Canary distribution package here instead of run-integ-buildspec.yml
    And upload file "{{cache:DistributionPackageRelativePath}}" as "{{cache:DistributionPackageS3Key}}" S3 key to ssm-test-resources S3 bucket and save locations to "CloudWatchCanary" cache property
    And the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                               | ResourceType | DocumentDbConnectionAttemptCanaryS3Bucket | DocumentDbConnectionAttemptCanaryS3Key | DocumentDbConnectionAttemptCanaryS3ObjectVersion | KmsKey                              |
      | resource_manager/cloud_formation_templates/shared/KMS.yml                                     | SHARED       |                                           |                                        |                                                  |                                     |
      | resource_manager/cloud_formation_templates/DocDbTemplate.yml                                  | ON_DEMAND    | {{cache:CloudWatchCanary>S3Bucket}}       | {{cache:CloudWatchCanary>S3Key}}       | {{cache:CloudWatchCanary>S3ObjectVersion}}       | {{cfn-output:KMS>EncryptAtRestKey}} |
      | documents/docdb/test/reboot_db_instance/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                                           |                                        |                                                  |                                     |
    And published "Digito-RebootDbInstance_2020-09-21" SSM document
    When SSM automation document "Digito-RebootDbInstance_2020-09-21" executed
      | DBClusterIdentifier                              | DBInstanceIdentifier                                     | AutomationAssumeRole                                                              | SyntheticAlarmName                                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} | {{cfn-output:DocDbTemplate>DBInstancePrimaryIdentifier}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoDocdbRebootDbInstanceAssumeRole}} | {{cfn-output:DocDbTemplate>DatabaseConnectionAttemptAlarmName}} |
    Then SSM automation document "Digito-RebootDbInstance_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |