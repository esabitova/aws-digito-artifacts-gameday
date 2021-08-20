@docdb @integration @alarm

Feature: Alarm Setup - DocumentDB HighReplicaLagMaximum

  Scenario: To detect high values of DBClusterReplicaLagMaximum - green
    Given the cached input parameters
      | DistributionPackageRelativePath                                                  | DistributionPackageS3Key         |
      | documents/docdb/canary/database-connection-canary/database-connection-canary.zip | canary/database-alarm-canary.zip |
    #todo DIG-977 create CW Canary distribution package here instead of run-integ-buildspec.yml
    And upload unique file "{{cache:DistributionPackageRelativePath}}" as "{{cache:DistributionPackageS3Key}}" S3 key to "ssm-docdb-test-resources" S3 bucket and save locations to "CloudWatchCanary" cache property
    And the cloud formation templates as integration test resources
      | CfnTemplatePath                                                               | ResourceType | VPC                      | VPCCIDR                    | PrivateSubnet01                                | PrivateSubnet02                                | PrivateSubnet03                                | DocumentDbConnectionAttemptCanaryS3Bucket | DocumentDbConnectionAttemptCanaryS3Key | DocumentDbConnectionAttemptCanaryS3ObjectVersion | CleanupS3BucketLambdaArn                                      | CleanupCanaryLambdaArn                                    | KmsKey                              |
      | resource_manager/cloud_formation_templates/shared/CleanupS3BucketLambda.yml   | SHARED       |                          |                            |                                                |                                                |                                                |                                           |                                        |                                                  |                                                               |                                                           |                                     |
      | resource_manager/cloud_formation_templates/shared/CleanupCanaryLambda.yml     | SHARED       |                          |                            |                                                |                                                |                                                |                                           |                                        |                                                  |                                                               |                                                           |                                     |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                     | SHARED       |                          |                            |                                                |                                                |                                                |                                           |                                        |                                                  |                                                               |                                                           |                                     |
      | resource_manager/cloud_formation_templates/shared/KMS.yml                     | SHARED       |                          |                            |                                                |                                                |                                                |                                           |                                        |                                                  |                                                               |                                                           |                                     |
      | resource_manager/cloud_formation_templates/DocDbTemplate.yml                  | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>VPCCidr}} | {{cfn-output:VPC>PrivateSubnetWithInternet01}} | {{cfn-output:VPC>PrivateSubnetWithInternet02}} | {{cfn-output:VPC>PrivateSubnetWithInternet03}} | {{cache:CloudWatchCanary>S3Bucket}}       | {{cache:CloudWatchCanary>S3Key}}       | {{cache:CloudWatchCanary>S3ObjectVersion}}       | {{cfn-output:CleanupS3BucketLambda>CleanupS3BucketLambdaArn}} | {{cfn-output:CleanupCanaryLambda>CleanupCanaryLambdaArn}} | {{cfn-output:KMS>EncryptAtRestKey}} |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml            | SHARED       |                          |                            |                                                |                                                |                                                |                                           |                                        |                                                  |                                                               |                                                           |                                     |

    When alarm "docdb:alarm:recovery-cluster_replica_lag:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | DBClusterIdentifier                              | Threshold |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} | 10000     |
    Then assert metrics for all alarms are populated
    And sleep for "30" seconds
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 300 seconds, check every 15 seconds

  Scenario: To detect high values of DBClusterReplicaLagMaximum - red
    Given the cached input parameters
      | DistributionPackageRelativePath                                                  | DistributionPackageS3Key         |
      | documents/docdb/canary/database-connection-canary/database-connection-canary.zip | canary/database-alarm-canary.zip |
    #todo DIG-977 create CW Canary distribution package here instead of run-integ-buildspec.yml
    And upload unique file "{{cache:DistributionPackageRelativePath}}" as "{{cache:DistributionPackageS3Key}}" S3 key to "ssm-docdb-test-resources" S3 bucket and save locations to "CloudWatchCanary" cache property
    And the cloud formation templates as integration test resources
      | CfnTemplatePath                                                               | ResourceType | VPC                      | VPCCIDR                    | PrivateSubnet01                                | PrivateSubnet02                                | PrivateSubnet03                                | DocumentDbConnectionAttemptCanaryS3Bucket | DocumentDbConnectionAttemptCanaryS3Key | DocumentDbConnectionAttemptCanaryS3ObjectVersion | CleanupS3BucketLambdaArn                                      | CleanupCanaryLambdaArn                                    | KmsKey                              |
      | resource_manager/cloud_formation_templates/shared/CleanupS3BucketLambda.yml   | SHARED       |                          |                            |                                                |                                                |                                                |                                           |                                        |                                                  |                                                               |                                                           |                                     |
      | resource_manager/cloud_formation_templates/shared/CleanupCanaryLambda.yml     | SHARED       |                          |                            |                                                |                                                |                                                |                                           |                                        |                                                  |                                                               |                                                           |                                     |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                     | SHARED       |                          |                            |                                                |                                                |                                                |                                           |                                        |                                                  |                                                               |                                                           |                                     |
      | resource_manager/cloud_formation_templates/shared/KMS.yml                     | SHARED       |                          |                            |                                                |                                                |                                                |                                           |                                        |                                                  |                                                               |                                                           |                                     |
      | resource_manager/cloud_formation_templates/DocDbTemplate.yml                  | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>VPCCidr}} | {{cfn-output:VPC>PrivateSubnetWithInternet01}} | {{cfn-output:VPC>PrivateSubnetWithInternet02}} | {{cfn-output:VPC>PrivateSubnetWithInternet03}} | {{cache:CloudWatchCanary>S3Bucket}}       | {{cache:CloudWatchCanary>S3Key}}       | {{cache:CloudWatchCanary>S3ObjectVersion}}       | {{cfn-output:CleanupS3BucketLambda>CleanupS3BucketLambdaArn}} | {{cfn-output:CleanupCanaryLambda>CleanupCanaryLambdaArn}} | {{cfn-output:KMS>EncryptAtRestKey}} |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml            | SHARED       |                          |                            |                                                |                                                |                                                |                                           |                                        |                                                  |                                                               |                                                           |                                     |

    When alarm "docdb:alarm:recovery-cluster_replica_lag:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | DBClusterIdentifier                              | Threshold |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} | 1         |
    Then assert metrics for all alarms are populated
    And sleep for "30" seconds
    And wait until alarm {{alarm:under_test>AlarmName}} becomes ALARM within 300 seconds, check every 15 seconds
