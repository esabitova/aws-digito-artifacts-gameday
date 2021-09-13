@kinesis-analytics
Feature: SSM automation document Digito-RestoreKinesisDataAnalyticsApplicationFromSnapshotSOP_2021-07-28

  Scenario: Execute Digito-RestoreKinesisDataAnalyticsApplicationFromSnapshotSOP_2021-07-28 to restore kinesis data analytics flink application from latest snapshot
     Given the cached input parameters
      | FlinkAppRelativePath                                       | FlinkAppS3Key                               | S3KinesisAnalyticsApplicationBucketNamePrefix | KinesisAnalyticsSnapshotName |
      | resource_manager/executables/flinkapp/python-test-sink.zip | kinesis-analytics-app/python-test-sink.zip  | kda-apache-flink-application-s3               | Latest                       |
    And create S3 bucket and save the bucket name as "S3KinesisAnalyticsApplicationBucketName" to "KinesisAnalytics" cache property
      | S3BucketNamePrefix                                      | S3BucketTeardown |
      | {{cache:S3KinesisAnalyticsApplicationBucketNamePrefix}} | Yes              |
    And upload Kinesis Data Analytics application file to S3 bucket with given key and save locations to "KinesisAnalytics" cache property       
      | S3KinesisAnalyticsApplicationBucketName                            | FlinkAppRelativePath           | FlinkAppS3Key           |
      | {{cache:KinesisAnalytics>S3KinesisAnalyticsApplicationBucketName}} | {{cache:FlinkAppRelativePath}} | {{cache:FlinkAppS3Key}} |
    And the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                                                | ResourceType | S3FlinkCodeBucket                   | FlinkApplicationObjectKey | KmsKey                              |
      | resource_manager/cloud_formation_templates/shared/KMS.yml                                                                      | SHARED       |                                     |                           |                                     |
      | resource_manager/cloud_formation_templates/KinesisAnalyticsTemplateFlink.yml                                                   | ON_DEMAND    | {{cache:KinesisAnalytics>S3Bucket}} | {{cache:FlinkAppS3Key}}   | {{cfn-output:KMS>EncryptAtRestKey}} |
      | documents/kinesis-analytics/sop/data_analytics_restore_app_from_snapshot/2021-07-28/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                                     |                           |                                     |
    And published "Digito-RestoreKinesisDataAnalyticsApplicationFromSnapshotSOP_2021-07-28" SSM document    
    And start Kinesis Data Analytics for "Apache Flink" application
      | KinesisAnalyticsAppName                                                                    |
      | {{cfn-output:KinesisAnalyticsTemplateFlink>KinesisAnalyticsApplicationPhysicalResourceId}} |
    And prove recovery snapshot exists and confect it otherwise
      | KinesisAnalyticsAppName                                                                    | KinesisAnalyticsInputSnapshotName      |
      | {{cfn-output:KinesisAnalyticsTemplateFlink>KinesisAnalyticsApplicationPhysicalResourceId}} | {{cache:KinesisAnalyticsSnapshotName}} |
    When SSM automation document "Digito-RestoreKinesisDataAnalyticsApplicationFromSnapshotSOP_2021-07-28" executed
      | KinesisAnalyticsFlinkApplication                                                           | AutomationAssumeRole                                                                                            |
      | {{cfn-output:KinesisAnalyticsTemplateFlink>KinesisAnalyticsApplicationPhysicalResourceId}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoKinesisAnalyticsDataAnalyticsRestoreAppFromSnapshotAssumeRole}} |
    Then SSM automation document "Digito-RestoreKinesisDataAnalyticsApplicationFromSnapshotSOP_2021-07-28" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |    
    And assert "RecordStartTime,CheckIfKinesisDataAnalyticsApplicationIsRunning,VerifyIfKinesisDataSnalyticsSnapshotExists,ObtainKinesisDataAnalyticsApplicationS3bucketObjectVersionId,
                ObtainKinesisDataAnalyticsApplicationConditionalToken,ChooseToRestoreFromLatestOrFromProvidedSnapshot,RecoveKinesisDataAnalyticsApplicationFromLatestSnapshot,
                WaitForKinesisDataAnalyticsSnapshotRecoveryCompletes,OutputRecoveryTime" steps are successfully executed in order
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache kinesis data analytics application restore type as "FlinkAppRestoreType" "after" SSM automation execution
      | KinesisAnalyticsAppName                                                                    |
      | {{cfn-output:KinesisAnalyticsTemplateFlink>KinesisAnalyticsApplicationPhysicalResourceId}} |
    And assert "FlinkAppRestoreType" at "after" became equal to "RESTORE_FROM_LATEST_SNAPSHOT"
