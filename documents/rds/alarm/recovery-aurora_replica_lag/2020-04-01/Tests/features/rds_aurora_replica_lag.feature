@rds @integration @alarm @aurora_lag
Feature: Alarm Setup - RDS Aurora replica lag
  Scenario: Lease RDS from resource manager and test attach an alarm from Document
    Given the cloud formation templates as integration test resources
      |CfnTemplatePath                                                               |ResourceType|DBInstanceClass|
      |resource_manager/cloud_formation_templates/RdsAuroraWithBacktrackTemplate.yml |   ON_DEMAND|    db.t3.small|
      |resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml            |SHARED      |               |
    And cache DB cluster "replicaId" and "dbWriterId" as "current"
      |ClusterId                                             |
      |{{cfn-output:RdsAuroraWithBacktrackTemplate>ClusterId}}|
    When alarm "rds:alarm:recovery-aurora_replica_lag:2020-04-01" is installed
      |alarmId    |DBInstanceIdentifier        | Threshold     | SNSTopicARN
      |under_test |{{cache:current>replicaId}} | 10000         | {{cfn-output:SnsForAlarms>Topic}}
    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 180 seconds, check every 15 seconds
