@backup @integration @alarm
Feature: Alarm Setup - Backup NumberOfBackupJobsAborted
  Scenario: Attach NumberOfBackupJobsAborted alarm to Document and trigger it
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                    | ResourceType |
      | resource_manager/cloud_formation_templates/BackupTemplate.yml      | ON_DEMAND    |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml | SHARED       |
    When alarm "backup:alarm:backup-jobs-aborted:2020-12-06" is installed
      | alarmId    | BackupVaultName                                          | Threshold | SNSTopicARN                       |
      | under_test | {{cfn-output:BackupTemplate>BackupVaultDestinationName}} | 0         | {{cfn-output:SnsForAlarms>Topic}} |
    Then issue a backup job for FileSystemId in BackupVaultDestinationName and immediately abort it
      | FileSystemId                               | BackupVaultDestinationName                               | BackupJobIamRoleArn                               |
      | {{cfn-output:BackupTemplate>FileSystemId}} | {{cfn-output:BackupTemplate>BackupVaultDestinationName}} | {{cfn-output:BackupTemplate>BackupJobIamRoleArn}} |
    And assert metrics for all alarms are populated within 1000 seconds, check every 15 seconds
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 180 seconds, check every 15 seconds
