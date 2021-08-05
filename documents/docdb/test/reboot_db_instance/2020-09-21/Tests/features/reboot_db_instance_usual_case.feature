@docdb
Feature: SSM automation document Digito-RebootDbInstance_2020-09-21

  Scenario: Execute SSM automation document Digito-RebootDbInstance_2020-09-21
    Given the cached input parameters
      | DistributionPackageRelativePath                                                  | DistributionPackageS3Key         |
      | documents/docdb/canary/database-connection-canary/database-connection-canary.zip | canary/database-alarm-canary.zip |
    #todo DIG-977 create CW Canary distribution package here instead of run-integ-buildspec.yml
    And upload file "{{cache:DistributionPackageRelativePath}}" as "{{cache:DistributionPackageS3Key}}" S3 key to ssm-test-resources S3 bucket and save locations to "CloudWatchCanary" cache property
    And the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                               | ResourceType | VPC                      | VPCCIDR                    | PrivateSubnet01                                | PrivateSubnet02                                | DocumentDbConnectionAttemptCanaryS3Bucket | DocumentDbConnectionAttemptCanaryS3Key | DocumentDbConnectionAttemptCanaryS3ObjectVersion | CleanupS3BucketLambdaArn                                      |
      | resource_manager/cloud_formation_templates/shared/CleanupS3BucketLambda.yml                   | SHARED       |                          |                            |                                                |                                                |                                           |                                        |                                                  |                                                               |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                                     | SHARED       |                          |                            |                                                |                                                |                                           |                                        |                                                  |                                                               |
      | resource_manager/cloud_formation_templates/DocDBWithCanaryTemplate.yml                        | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>VPCCidr}} | {{cfn-output:VPC>PrivateSubnetWithInternet01}} | {{cfn-output:VPC>PrivateSubnetWithInternet02}} | {{cache:CloudWatchCanary>S3Bucket}}       | {{cache:CloudWatchCanary>S3Key}}       | {{cache:CloudWatchCanary>S3ObjectVersion}}       | {{cfn-output:CleanupS3BucketLambda>CleanupS3BucketLambdaArn}} |
      | documents/docdb/test/reboot_db_instance/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                          |                            |                                                |                                                |                                           |                                        |                                                  |                                                               |
    And published "Digito-RebootDbInstance_2020-09-21" SSM document
    When SSM automation document "Digito-RebootDbInstance_2020-09-21" executed
      | DBClusterIdentifier                                        | DBInstanceIdentifier                                               | AutomationAssumeRole                                                              | SyntheticAlarmName                                                        |
      | {{cfn-output:DocDBWithCanaryTemplate>DBClusterIdentifier}} | {{cfn-output:DocDBWithCanaryTemplate>DBInstancePrimaryIdentifier}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoDocdbRebootDbInstanceAssumeRole}} | {{cfn-output:DocDBWithCanaryTemplate>DatabaseConnectionAttemptAlarmName}} |
    Then SSM automation document "Digito-RebootDbInstance_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |