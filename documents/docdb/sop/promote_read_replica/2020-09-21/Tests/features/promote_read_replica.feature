@docdb
Feature: SSM automation document to promote read replica.

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document for promoting DocDb replica to the primary instance
    Given the cached input parameters
      | DistributionPackageRelativePath                                                  | DistributionPackageS3Key         |
      | documents/docdb/canary/database-connection-canary/database-connection-canary.zip | canary/database-alarm-canary.zip |
    #todo DIG-977 create CW Canary distribution package here instead of run-integ-buildspec.yml
    And upload file "{{cache:DistributionPackageRelativePath}}" as "{{cache:DistributionPackageS3Key}}" S3 key to S3 bucket with prefix "ssm-docdb-test-resources" and save locations to "CloudWatchCanary" cache property
    And the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                | ResourceType | VPC                      | VPCCIDR                    | PrivateSubnet01                                | PrivateSubnet02                                | DocumentDbConnectionAttemptCanaryS3Bucket | DocumentDbConnectionAttemptCanaryS3Key | DocumentDbConnectionAttemptCanaryS3ObjectVersion | CleanupS3BucketLambdaArn                                      | CleanupCanaryLambdaArn                                    | KmsKey                              |
      | resource_manager/cloud_formation_templates/shared/CleanupS3BucketLambda.yml                    | SHARED       |                          |                            |                                                |                                                |                                           |                                        |                                                  |                                                               |                                                           |                                     |
      | resource_manager/cloud_formation_templates/shared/CleanupCanaryLambda.yml                      | SHARED       |                          |                            |                                                |                                                |                                           |                                        |                                                  |                                                               |                                                           |                                     |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                                      | SHARED       |                          |                            |                                                |                                                |                                           |                                        |                                                  |                                                               |                                                           |                                     |
      | resource_manager/cloud_formation_templates/shared/KMS.yml                                      | SHARED       |                          |                            |                                                |                                                |                                           |                                        |                                                  |                                                               |                                                           |                                     |
      | resource_manager/cloud_formation_templates/DocDbTemplate.yml                                   | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>VPCCidr}} | {{cfn-output:VPC>PrivateSubnetWithInternet01}} | {{cfn-output:VPC>PrivateSubnetWithInternet02}} | {{cache:CloudWatchCanary>S3Bucket}}       | {{cache:CloudWatchCanary>S3Key}}       | {{cache:CloudWatchCanary>S3ObjectVersion}}       | {{cfn-output:CleanupS3BucketLambda>CleanupS3BucketLambdaArn}} | {{cfn-output:CleanupCanaryLambda>CleanupCanaryLambdaArn}} | {{cfn-output:KMS>EncryptAtRestKey}} |
      | documents/docdb/sop/promote_read_replica/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                          |                            |                                                |                                                |                                           |                                        |                                                  |                                                               |                                                           |                                     |
    And published "Digito-PromoteReadReplica_2020-09-21" SSM document
    And cache replica instance identifier as "DBInstanceReplicaIdentifier" at step "before"
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    When SSM automation document "Digito-PromoteReadReplica_2020-09-21" executed
      | DBClusterIdentifier                              | DBInstanceReplicaIdentifier                  | AutomationAssumeRole                                                           |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} | {{cache:before>DBInstanceReplicaIdentifier}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoPromoteReadReplicaAssumeRole}} |

    Then SSM automation document "Digito-PromoteReadReplica_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And sleep for "120" seconds
    And assert if the cluster member is the primary instance
      | DBClusterIdentifier                              | DBInstanceIdentifier                         |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} | {{cache:before>DBInstanceReplicaIdentifier}} |
