@redshift @integration @alarm
Feature: Alarm Setup - Amazon Redshift Cluster_percent_quota_used
  Scenario: Create redshift:alarm:percent_quota_used:2020-04-01 based on PercentageQuotaUsed metric and check OK status
    Given install dependencies from requirement file, build Lambda distribution package, and save package path to "RedshiftLambdaPackagePath" cache property
      | RequirementsFileRelationalPath                                                                                    | DirectoryWithCodeRelationalPath                                                                  |
      | resource_manager/cloud_formation_templates/lambda_dependencies/redshift/redshift_performance/src/requirements.txt | resource_manager/cloud_formation_templates/lambda_dependencies/redshift/redshift_performance/src |
    And the cached input parameters
      | RedshiftDistributionPackageS3Key               |
      | packages/alarm/trigger_concurrency_scaling.zip |
    And upload file "{{cache:RedshiftLambdaPackagePath}}" as "{{cache:RedshiftDistributionPackageS3Key}}" S3 key to S3 bucket with prefix "redshift-test-resources" and save locations to "RedshiftPerformanceLambdaPackage" cache property
    And the cloud formation templates as integration test resources
      | CfnTemplatePath                                                    | ResourceType | KmsKey                              | VPC                      | PublicSubnetOne                    | PublicSubnetTwo                    | PublicSubnet1Cidr                    | PublicSubnet2Cidr                    | RedshiftPerformanceLambdaPackageS3Bucket            | RedshiftPerformanceLambdaPackageS3Key            | RedshiftPerformanceLambdaPackageS3BucketObjectVersion      |
      | resource_manager/cloud_formation_templates/shared/KMS.yml          | SHARED       |                                     |                          |                                    |                                    |                                      |                                      |                                                     |                                                  |                                                            |
      | resource_manager/cloud_formation_templates/shared/VPC.yml          | SHARED       |                                     |                          |                                    |                                    |                                      |                                      |                                                     |                                                  |                                                            |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml | SHARED       |                                     |                          |                                    |                                    |                                      |                                      |                                                     |                                                  |                                                            |
      | resource_manager/cloud_formation_templates/RedshiftTemplate.yml    | ON_DEMAND    | {{cfn-output:KMS>EncryptAtRestKey}} | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>PublicSubnetOne}} | {{cfn-output:VPC>PublicSubnetTwo}} | {{cfn-output:VPC>PublicSubnet1Cidr}} | {{cfn-output:VPC>PublicSubnet2Cidr}} | {{cache:RedshiftPerformanceLambdaPackage>S3Bucket}} | {{cache:RedshiftPerformanceLambdaPackage>S3Key}} | {{cache:RedshiftPerformanceLambdaPackage>S3ObjectVersion}} |
    And trigger lambda "{{cfn-output:RedshiftTemplate>LambdaArn}}" asynchronously
    When alarm "redshift:alarm:percent_quota_used:2020-04-01" is installed
      | alarmId    | ClusterName                                 | DatabaseName                                 | SchemaName                                 | Threshold | EvaluationPeriods | DatapointsToAlarm | SNSTopicARN                       |
      | under_test | {{cfn-output:RedshiftTemplate>ClusterName}} | {{cfn-output:RedshiftTemplate>DatabaseName}} | {{cfn-output:RedshiftTemplate>SchemaName}} | 80        | 1                 | 1                 | {{cfn-output:SnsForAlarms>Topic}} |
    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 300 seconds, check every 15 seconds


