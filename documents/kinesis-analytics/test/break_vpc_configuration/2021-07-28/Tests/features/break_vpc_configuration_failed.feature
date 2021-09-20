@kinesis-analytics
Feature: SSM automation document Digito-BreakKinesisDataAnalyticsVpcConfigurationTest_2021-07-28
  
  Scenario: Execute SSM automation document Digito-BreakKinesisDataAnalyticsVpcConfigurationTest_2021-07-28 to test failure case
    Given the cached input parameters
      | FlinkAppRelativePath                                       | FlinkAppS3Key                               | S3KinesisAnalyticsApplicationBucketNamePrefix |
      | resource_manager/executables/flinkapp/python-test-sink.zip | kinesis-analytics-app/python-test-sink.zip  | kda-apache-flink-application-s3               |
    And create S3 bucket and save the bucket name as "S3KinesisAnalyticsApplicationBucketName" to "KinesisAnalytics" cache property
      | S3BucketNamePrefix                                      | S3BucketTeardown |
      | {{cache:S3KinesisAnalyticsApplicationBucketNamePrefix}} | Yes              |
    And upload Kinesis Data Analytics application file to S3 bucket with given key and save locations to "KinesisAnalytics" cache property       
      | S3KinesisAnalyticsApplicationBucketName                            | FlinkAppRelativePath           | FlinkAppS3Key           |
      | {{cache:KinesisAnalytics>S3KinesisAnalyticsApplicationBucketName}} | {{cache:FlinkAppRelativePath}} | {{cache:FlinkAppS3Key}} |
    And the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                                | ResourceType | S3FlinkCodeBucket                                                  | FlinkApplicationObjectKey | KmsKey                              | PrivateSubnetKDA                                   | VPC                      | SubnetCidr                            |
      | resource_manager/cloud_formation_templates/shared/KMS.yml                                                      | SHARED       |                                                                    |                           |                                     |                                                    |                          |                                       |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                                                      | SHARED       |                                                                    |                           |                                     |                                                    |                          |                                       |
      | resource_manager/cloud_formation_templates/shared/CommonAlarms.yml                                             | SHARED       |                                                                    |                           |                                     |                                                    |                          |                                       |
      | resource_manager/cloud_formation_templates/KinesisAnalyticsTemplateFlinkVPC.yml                                | ON_DEMAND    | {{cache:KinesisAnalytics>S3KinesisAnalyticsApplicationBucketName}} | {{cache:FlinkAppS3Key}}   | {{cfn-output:KMS>EncryptAtRestKey}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetOne}} | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>PrivateSubnet1Cidr}} |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml                                             | SHARED       |                                                                    |                           |                                     |                                                    |                          |                                       |
      | documents/kinesis-analytics/test/break_vpc_configuration/2021-07-28/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                                                                    |                           |                                     |                                                    |                          |                                       |
    And start Kinesis Data Analytics for "Apache Flink" application
      | KinesisAnalyticsAppName                                                                       |
      | {{cfn-output:KinesisAnalyticsTemplateFlinkVPC>KinesisAnalyticsApplicationPhysicalResourceId}} |
    And prove kinesis data analytics application is either in provided VPC or add to provided VPC otherwise
      | KinesisAnalyticsAppName                                                                       | VpcId                     | SubnetId                                            | SecurityGroupsIdList                                                                     |
      | {{cfn-output:KinesisAnalyticsTemplateFlinkVPC>KinesisAnalyticsApplicationPhysicalResourceId}} | {{cfn-output:VPC>VPCId}}  | {{cfn-output:VPC>PrivateSubnetWithoutInternetOne}}  | {{cfn-output:KinesisAnalyticsTemplateFlinkVPC>KinesisDataAnalyticsSecurityGroupsIdList}} |
    And published "Digito-BreakKinesisDataAnalyticsVpcConfigurationTest_2021-07-28" SSM document
    And cache Kinesis Data Analytics security group ids and save as "KinesisDataAnalyticsVpcSecurityGroup" at "before" SSM automation execution
      | KinesisAnalyticsAppName                                                                       |
      | {{cfn-output:KinesisAnalyticsTemplateFlinkVPC>KinesisAnalyticsApplicationPhysicalResourceId}} |
    And populate input stream by lambda loader "78" times
      | InputStreamLambdaLoaderName                                                 |
      | {{cfn-output:KinesisAnalyticsTemplateFlinkVPC>InputStreamLambdaLoaderName}} |
    When SSM automation document "Digito-BreakKinesisDataAnalyticsVpcConfigurationTest_2021-07-28" executed
      | KinesisAnalyticsFlinkApplicationId                                                            | AutomationAssumeRole                                                                              | DowntimeAlarmName                            |
      | {{cfn-output:KinesisAnalyticsTemplateFlinkVPC>KinesisAnalyticsApplicationPhysicalResourceId}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoKinesisAnalyticsBreakVpcConfigurationAssumeRole}} | {{cfn-output:CommonAlarms>AlwaysOKAlarmName}} |
    
    And Wait for the SSM automation document "Digito-BreakKinesisDataAnalyticsVpcConfigurationTest_2021-07-28" execution is on step "AssertAlarmToBeRed" in status "TimedOut"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |       
    Then SSM automation document "Digito-BreakKinesisDataAnalyticsVpcConfigurationTest_2021-07-28" execution in status "TimedOut"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache Kinesis Data Analytics security group ids and save as "KinesisDataAnalyticsVpcSecurityGroup" at "after" SSM automation execution
      | KinesisAnalyticsAppName                                                                       |
      | {{cfn-output:KinesisAnalyticsTemplateFlinkVPC>KinesisAnalyticsApplicationPhysicalResourceId}} |
    And assert "KinesisDataAnalyticsVpcSecurityGroup" at "before" became equal to "KinesisDataAnalyticsVpcSecurityGroup" at "after"
    And assert "CheckIsRollback,AssertAlarmToBeGreenBeforeTest,CheckKinesisDataAnalyticsApplicationVPCStatus,AwaitKinesisDataAnalyticsRunningStatusBeforeBackupCurrentExecution,
                BackupCurrentExecution,CreateDummySecurityGroup,InjectFailure,AwaitApplicationUpdateCompleteAfterInjectFailure,RollbackCurrentExecution,
                AwaitApplicationIsRunningAfterRollbackCurrentExecution,RemoveDummySecurityGroupAfterRollbackCurrentExecution,AssertAlarmToBeGreen" steps are successfully executed in order
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    