@docdb
Feature: SSM automation document to test database alarm.

  Scenario: Test database alarm SSM execution in rollback
    Given the cached input parameters
      | DistributionPackageRelativePath                                                  | DistributionPackageS3Key         |
      | documents/docdb/canary/database-connection-canary/database-connection-canary.zip | canary/database-alarm-canary.zip |
    #todo DIG-977 create CW Canary distribution package here instead of run-integ-buildspec.yml
    And upload file "{{cache:DistributionPackageRelativePath}}" as "{{cache:DistributionPackageS3Key}}" S3 key to S3 bucket with prefix "ssm-docdb-test-resources" and save locations to "CloudWatchCanary" cache property
    And the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                        | ResourceType | VPC                      | VPCCIDR                    | PrivateSubnet01                                | PrivateSubnet02                                |  DocumentDbConnectionAttemptCanaryS3Bucket | DocumentDbConnectionAttemptCanaryS3Key | DocumentDbConnectionAttemptCanaryS3ObjectVersion | CleanupS3BucketLambdaArn                                      | CleanupCanaryLambdaArn                                    | KmsKey                              |
      | resource_manager/cloud_formation_templates/shared/CleanupS3BucketLambda.yml                            | SHARED       |                          |                            |                                                |                                                |                                            |                                        |                                                  |                                                               |                                                           |                                     |
      | resource_manager/cloud_formation_templates/shared/CleanupCanaryLambda.yml                              | SHARED       |                          |                            |                                                |                                                |                                            |                                        |                                                  |                                                               |                                                           |                                     |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                                              | SHARED       |                          |                            |                                                |                                                |                                            |                                        |                                                  |                                                               |                                                           |                                     |
      | resource_manager/cloud_formation_templates/shared/KMS.yml                                              | SHARED       |                          |                            |                                                |                                                |                                            |                                        |                                                  |                                                               |                                                           |                                     |
      | resource_manager/cloud_formation_templates/DocDbTemplate.yml                                           | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>VPCCidr}} | {{cfn-output:VPC>PrivateSubnetWithInternet01}} | {{cfn-output:VPC>PrivateSubnetWithInternet02}} |  {{cache:CloudWatchCanary>S3Bucket}}       | {{cache:CloudWatchCanary>S3Key}}       | {{cache:CloudWatchCanary>S3ObjectVersion}}       | {{cfn-output:CleanupS3BucketLambda>CleanupS3BucketLambdaArn}} | {{cfn-output:CleanupCanaryLambda>CleanupCanaryLambdaArn}} | {{cfn-output:KMS>EncryptAtRestKey}} |
      | documents/docdb/test/database_inaccessible_alarm/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                          |                            |                                                |                                                |                                            |                                        |                                                  |                                                               |                                                           |                                     |
    And published "Digito-ForceDocumentDBDatabaseToBeInaccessibleTest_2020-09-21" SSM document
    And cache cluster vpc security groups as "VpcSecurityGroupsIds" at step "before" SSM automation execution
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |

    When SSM automation document "Digito-ForceDocumentDBDatabaseToBeInaccessibleTest_2020-09-21" executed
      | DBClusterIdentifier                              | AutomationAssumeRole                                                                                    | DatabaseConnectionAttemptAlarmName                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoForceDocumentDBDatabaseToBeInaccessibleTestAssumeRole}} | {{cfn-output:DocDbTemplate>DatabaseConnectionAttemptAlarmName}} |

    And Wait for the SSM automation document "Digito-ForceDocumentDBDatabaseToBeInaccessibleTest_2020-09-21" execution is on step "AssertAlarmToBeRed" in status "InProgress"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And terminate "Digito-ForceDocumentDBDatabaseToBeInaccessibleTest_2020-09-21" SSM automation document
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    Then Wait for the SSM automation document "Digito-ForceDocumentDBDatabaseToBeInaccessibleTest_2020-09-21" execution is on step "TriggerRollback" in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And SSM automation document "Digito-ForceDocumentDBDatabaseToBeInaccessibleTest_2020-09-21" execution in status "Cancelled"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache rollback execution id
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And SSM automation document "Digito-ForceDocumentDBDatabaseToBeInaccessibleTest_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>2}} |

    And cache cluster vpc security groups as "VpcSecurityGroupsIds" at step "after" SSM automation execution
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    When cache execution output value of "CreateEmptySecurityGroup.EmptySecurityGroupId" as "EmptySecurityGroupId" after SSM automation execution
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    Then assert "VpcSecurityGroupsIds" at "before" became equal to "VpcSecurityGroupsIds" at "after"
    And assert security group "EmptySecurityGroupId" at "after" was removed
