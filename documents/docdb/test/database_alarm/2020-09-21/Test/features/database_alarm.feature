@docdb
Feature: SSM automation document to test database alarm.

  Scenario: Test database alarm
    Given the cached input parameters
      | DistributionPackageRelativePath                                                      | DistributionPackageS3Key         |
      | documents/docdb/test/database_alarm/2020-09-21/Test/canary/database-alarm-canary.zip | canary/database-alarm-canary.zip |
    #todo DIG-977 create CW Canary distribution package here instead of run-integ-buildspec.yml
    And upload file "{{cache:DistributionPackageRelativePath}}" as "{{cache:DistributionPackageS3Key}}" S3 key to ssm-test-resources S3 bucket and save locations to "CloudWatchCanary" cache property
    And the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                           | ResourceType | DocumentDbConnectionAttemptCanaryS3Bucket | DocumentDbConnectionAttemptCanaryS3Key | DocumentDbConnectionAttemptCanaryS3ObjectVersion |
      | resource_manager/cloud_formation_templates/DocDbTemplate.yml                              | ON_DEMAND    | {{cache:CloudWatchCanary>S3Bucket}}       | {{cache:CloudWatchCanary>S3Key}}       | {{cache:CloudWatchCanary>S3ObjectVersion}}       |
      | documents/docdb/test/database_alarm/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                                           |                                        |                                                  |
    And published "Digito-DocDbDatabaseAlarm_2020-09-21" SSM document

    When SSM automation document "Digito-DocDbDatabaseAlarm_2020-09-21" executed
      | DBClusterIdentifier                              | AutomationAssumeRole                                                           | DatabaseConnectionAttemptAlarmName                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoDocDbDatabaseAlarmAssumeRole}} | {{cfn-output:DocDbTemplate>DatabaseConnectionAttemptAlarmName}} |
    And start canary
      | CanaryName                                                         |
      | {{cfn-output:DocDbTemplate>DocumentDbConnectionAttemptCanaryName}} |

    Then SSM automation document "Digito-DocDbDatabaseAlarm_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And assert "CheckIsRollback, AssertDBClusterExistsInAvailableState, AssertAlarmToBeGreenBeforeTest, BackupDbClusterProperties, GetOneOfSubnets, GetVpc, CreateEmptySecurityGroup, ModifyVpcSecurityGroups, AssertAlarmTriggered, AssertClusterIsAvailable, AssertInstancesAreAvailable, RestoreSecurityGroupIds, RemoveEmptySecurityGroup, AssertAlarmToBeGreen" steps are successfully executed in order
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
