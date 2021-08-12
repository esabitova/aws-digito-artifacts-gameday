@docdb
Feature: SSM automation document for scaling down DocDb instances.

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document for scaling down DocumentDb instances
    Given the cached input parameters
      | DistributionPackageRelativePath                                                  | DistributionPackageS3Key         |
      | documents/docdb/canary/database-connection-canary/database-connection-canary.zip | canary/database-alarm-canary.zip |
    #todo DIG-977 create CW Canary distribution package here instead of run-integ-buildspec.yml
    And upload file "{{cache:DistributionPackageRelativePath}}" as "{{cache:DistributionPackageS3Key}}" S3 key to ssm-test-resources S3 bucket and save locations to "CloudWatchCanary" cache property
    And the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                           | ResourceType | VPC                      | VPCCIDR                    | PrivateSubnet01                                | PrivateSubnet02                                | DocumentDbConnectionAttemptCanaryS3Bucket | DocumentDbConnectionAttemptCanaryS3Key | DocumentDbConnectionAttemptCanaryS3ObjectVersion | CleanupS3BucketLambdaArn                                      | CleanupCanaryLambdaArn                                    | KmsKey                              |
      | resource_manager/cloud_formation_templates/shared/CleanupS3BucketLambda.yml               | SHARED       |                          |                            |                                                |                                                |                                           |                                        |                                                  |                                                               |                                                           |                                     |
      | resource_manager/cloud_formation_templates/shared/CleanupCanaryLambda.yml                 | SHARED       |                          |                            |                                                |                                                |                                           |                                        |                                                  |                                                               |                                                           |                                     |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                                 | SHARED       |                          |                            |                                                |                                                |                                           |                                        |                                                  |                                                               |                                                           |                                     |
      | resource_manager/cloud_formation_templates/shared/KMS.yml                                 | SHARED       |                          |                            |                                                |                                                |                                           |                                        |                                                  |                                                               |                                                           |                                     |
      | resource_manager/cloud_formation_templates/DocDBTemplate.yml                    | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>VPCCidr}} | {{cfn-output:VPC>PrivateSubnetWithInternet01}} | {{cfn-output:VPC>PrivateSubnetWithInternet02}} | {{cache:CloudWatchCanary>S3Bucket}}       | {{cache:CloudWatchCanary>S3Key}}       | {{cache:CloudWatchCanary>S3ObjectVersion}}       | {{cfn-output:CleanupS3BucketLambda>CleanupS3BucketLambdaArn}} | {{cfn-output:CleanupCanaryLambda>CleanupCanaryLambdaArn}} | {{cfn-output:KMS>EncryptAtRestKey}} |
      | documents/docdb/sop/scaling_down/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml        | ASSUME_ROLE  |                          |                            |                                                |                                                |                                     |                                          |                                                  |                                                               |                                                           |                                     |
      | documents/docdb/sop/scaling_up/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml          | ASSUME_ROLE  |                          |                            |                                                |                                                |                                     |                                          |                                                  |                                                               |                                                           |                                     |
    And published "Digito-ScalingDown_2020-09-21" SSM document
    And published "Digito-ScalingUp_2020-09-21" SSM document
    And cache current number of instances as "NumberOfInstances" "before" SSM automation execution
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDBTemplate>DBClusterIdentifier}} |
    And SSM automation document "Digito-ScalingDown_2020-09-21" executed
      | DBClusterIdentifier                              | DBInstanceReplicaIdentifier                              | AutomationAssumeRole                                                    |
      | {{cfn-output:DocDBTemplate>DBClusterIdentifier}} | {{cfn-output:DocDBTemplate>DBInstanceReplicaIdentifier}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoScalingDownAssumeRole}} |

    When SSM automation document "Digito-ScalingDown_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache current number of instances as "NumberOfInstances" "after" SSM automation execution
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDBTemplate>DBClusterIdentifier}} |

    Then assert "NumberOfInstances" at "before" became not equal to "NumberOfInstances" at "after"
    And SSM automation document "Digito-ScalingUp_2020-09-21" executed
      | DBClusterIdentifier                              | DBInstanceReplicaIdentifier                              | AutomationAssumeRole                                                  |
      | {{cfn-output:DocDBTemplate>DBClusterIdentifier}} | {{cfn-output:DocDBTemplate>DBInstanceReplicaIdentifier}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoScalingUpAssumeRole}} |

    When SSM automation document "Digito-ScalingUp_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>2}} |
    And cache current number of instances as "NumberOfInstances" "finally" SSM automation execution
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDBTemplate>DBClusterIdentifier}} |
    Then assert "NumberOfInstances" at "before" became equal to "NumberOfInstances" at "finally"

