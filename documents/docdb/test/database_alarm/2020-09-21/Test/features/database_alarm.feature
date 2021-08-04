@docdb
Feature: SSM automation document to test database alarm.

  Scenario: Test database alarm
    Given the cached input parameters
      | DistributionPackageRelativePath                                                  | DistributionPackageS3Key         |
      | documents/docdb/canary/database-connection-canary/database-connection-canary.zip | canary/database-alarm-canary.zip |
    #todo DIG-977 create CW Canary distribution package here instead of run-integ-buildspec.yml
    And upload file "{{cache:DistributionPackageRelativePath}}" as "{{cache:DistributionPackageS3Key}}" S3 key to ssm-test-resources S3 bucket and save locations to "CloudWatchCanary" cache property
    And the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                           | ResourceType | VPC                      | VPCCIDR                    | PrivateSubnet01                                | PrivateSubnet02                                    | DocumentDbConnectionAttemptCanaryS3Bucket | DocumentDbConnectionAttemptCanaryS3Key | DocumentDbConnectionAttemptCanaryS3ObjectVersion | CleanupS3BucketLambdaArn                                 |
      | resource_manager/cloud_formation_templates/shared/CleanupS3BucketLambda.yml               | SHARED       |                          |                            |                                                |                                                    |                                           |                                        |                                                  |                                                          |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                                 | SHARED       |                          |                            |                                                |                                                    |                                           |                                        |                                                  |                                                          |
      | resource_manager/cloud_formation_templates/DocDBWithCanaryTemplate.yml                    | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>VPCCidr}} | {{cfn-output:VPC>PrivateSubnetWithInternet01}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetTwo}} | {{cache:CloudWatchCanary>S3Bucket}}       | {{cache:CloudWatchCanary>S3Key}}       | {{cache:CloudWatchCanary>S3ObjectVersion}}       | {{cfn-output:CleanupS3BucketLambda>CleanupS3BucketLambdaArn}} |
      | documents/docdb/test/database_alarm/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                          |                            |                                                |                                                    |                                           |                                        |                                                  |                                                          |
    And published "Digito-DocDbDatabaseAlarm_2020-09-21" SSM document
    And cache cluster vpc security groups as "VpcSecurityGroupsIds" at step "before" SSM automation execution
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDBWithCanaryTemplate>DBClusterIdentifier}} |

    When SSM automation document "Digito-DocDbDatabaseAlarm_2020-09-21" executed
      | DBClusterIdentifier                              | AutomationAssumeRole                                                           | DatabaseConnectionAttemptAlarmName                              |
      | {{cfn-output:DocDBWithCanaryTemplate>DBClusterIdentifier}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoDocDbDatabaseAlarmAssumeRole}} | {{cfn-output:DocDBWithCanaryTemplate>DatabaseConnectionAttemptAlarmName}} |
    And start canary
      | CanaryName                                                         |
      | {{cfn-output:DocDBWithCanaryTemplate>DocumentDbConnectionAttemptCanaryName}} |

    Then SSM automation document "Digito-DocDbDatabaseAlarm_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And assert "CheckIsRollback, AssertDBClusterExistsInAvailableState, AssertAlarmToBeGreenBeforeTest, BackupDbClusterProperties, GetOneOfSubnets, GetVpc, CreateEmptySecurityGroup, ModifyVpcSecurityGroups, AssertAlarmToBeRed, AssertClusterIsAvailable, AssertInstancesAreAvailable, RestoreSecurityGroupIds, RemoveEmptySecurityGroup, AssertAlarmToBeGreen" steps are successfully executed in order
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache cluster vpc security groups as "VpcSecurityGroupsIds" at step "after" SSM automation execution
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDBWithCanaryTemplate>DBClusterIdentifier}} |
    When cache execution output value of "CreateEmptySecurityGroup.EmptySecurityGroupId" as "EmptySecurityGroupId" after SSM automation execution
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    Then assert "VpcSecurityGroupsIds" at "before" became equal to "VpcSecurityGroupsIds" at "after"
    And assert security group "EmptySecurityGroupId" at "after" was removed
