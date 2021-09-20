@backup @integration @alarm
Feature: Alarm Setup - Backup NumberOfRestoreJobsFailed
  Scenario: Attach NumberOfRestoreJobsFailed alarm to Document and trigger it
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                    | ResourceType |
      | resource_manager/cloud_formation_templates/BackupTemplate.yml      | ON_DEMAND    |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml | SHARED       |
    When alarm "backup:alarm:restore-jobs-failed:2020-12-06" is installed
      | alarmId    | BackupVaultName                                          | Threshold | SNSTopicARN                       |
      | under_test | {{cfn-output:BackupTemplate>BackupVaultDestinationName}} | 0         | {{cfn-output:SnsForAlarms>Topic}} |
    # Cannot populate metrics in a synthetic test; reporting criteria omits zero values as per
    # https://docs.aws.amazon.com/aws-backup/latest/devguide/cloudwatch.html
    Then wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 180 seconds, check every 15 seconds
