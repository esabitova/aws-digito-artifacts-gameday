@kinesis-analytics
Feature: SSM automation document Digito-StopKinesisDataAnalyticsApplicationTest_2021-07-28

  Scenario: Execute SSM automation document Digito-StopKinesisDataAnalyticsApplicationTest_2021-07-28 in rollback test
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
      | CfnTemplatePath                                                                                                        | ResourceType | S3FlinkCodeBucket                   | FlinkApplicationObjectKey | KmsKey                              |
      | resource_manager/cloud_formation_templates/shared/KMS.yml                                                              | SHARED       |                                     |                           |                                     |
      | resource_manager/cloud_formation_templates/KinesisAnalyticsTemplateFlink.yml                                           | ON_DEMAND    | {{cache:KinesisAnalytics>S3Bucket}} | {{cache:FlinkAppS3Key}}   | {{cfn-output:KMS>EncryptAtRestKey}} |
      | documents/kinesis-analytics/test/stop_application/2021-07-28/Documents/AutomationAssumeRoleTemplate.yml                | ASSUME_ROLE  |                                     |                           |                                     |
    And published "Digito-StopKinesisDataAnalyticsApplicationTest_2021-07-28" SSM document    
    And cache Kinesis Data Analytics for "Apache Flink" application InputId as KinesisAnalyticsInputId and OutputId as KinesisAnalyticsOutputId "before" SSM automation execution
      | KinesisAnalyticsApplicationName                                                            |
      | {{cfn-output:KinesisAnalyticsTemplateFlink>KinesisAnalyticsApplicationPhysicalResourceId}} |
    And start Kinesis Data Analytics for "Apache Flink" application
      | KinesisAnalyticsAppName                                                                    |
      | {{cfn-output:KinesisAnalyticsTemplateFlink>KinesisAnalyticsApplicationPhysicalResourceId}} |    
    And populate input stream with random ticker data for "60" seconds
      | InputStreamName                                                              |
      | {{cfn-output:KinesisAnalyticsTemplateFlink>InputKinesisAnalyticsStreamName}} |
    
    When SSM automation document "Digito-StopKinesisDataAnalyticsApplicationTest_2021-07-28" executed
      | KinesisAnalyticsFlinkApplicationId                                                         | AutomationAssumeRole                                                                        | DowntimeAlarmName                                              |
      | {{cfn-output:KinesisAnalyticsTemplateFlink>KinesisAnalyticsApplicationPhysicalResourceId}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoKinesisAnalyticsStopApplicationAssumeRole}} | {{cfn-output:KinesisAnalyticsTemplateFlink>DowntimeAlarmName}} |
    And Wait for the SSM automation document "Digito-StopApplication_2021-07-28" execution is on step "AssertAlarmToBeRed" in status "InProgress"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And terminate "Digito-StopKinesisDataAnalyticsApplicationTest_2021-07-28" SSM automation document
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    Then Wait for the SSM automation document "Digito-StopKinesisDataAnalyticsApplicationTest_2021-07-28" execution is on step "TriggerRollback" in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And SSM automation document "Digito-StopKinesisDataAnalyticsApplicationTest_2021-07-28" execution in status "Cancelled"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache rollback execution id
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    Then SSM automation document "Digito-StopKinesisDataAnalyticsApplicationTest_2021-07-28" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>2}} |
    And assert SSM automation document step "RollbackOfPreviousExecution" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>2}} |
    And get Kinesis Data Analytics application status code and cache as "ApplicationStatusCodeAfterRollbackCurrentExecution" "after" SSM automation execution
      | KinesisAnalyticsAppName                                                                    |
      | {{cfn-output:KinesisAnalyticsTemplateFlink>KinesisAnalyticsApplicationPhysicalResourceId}} |
    
    Then assert "ApplicationStatusCodeAfterRollbackCurrentExecution" at "after" became equal to "200"
    And assert "CheckIsRollback,AssertAlarmToBeGreenBeforeTest,InjectFailure,AwaitApplicationHasStopped,TriggerRollback" steps are successfully executed in order
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And assert "CheckIsRollback,GetInputsFromPreviousExecution,AssertInputsFromPreviousExecution,ObtainKinesisDataAnalyticsApplicationStatus,
                VerifyKinesisDataAnalyticsStatus,RollbackOfPreviousExecution,AwaitKinesisDataAnalyticsApplicationGetRunning" steps are successfully executed in order
      | ExecutionId                |
      | {{cache:SsmExecutionId>2}} |
