@docdb @integration @alarm

Feature: Alarm Setup - DocumentDB LowCPUCreditBalance

  Scenario: To detect low values of CPUCreditBalance - green
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                    | ResourceType |                                     |
      | resource_manager/cloud_formation_templates/shared/KMS.yml          | SHARED       |                                     |
      | resource_manager/cloud_formation_templates/DocDbTemplate.yml       | ON_DEMAND    | {{cfn-output:KMS>EncryptAtRestKey}} |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml | SHARED       |                                     |
    When alarm "docdb:alarm:health-cpu_credit_balance:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | DBInstanceIdentifier                                     | Threshold |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:DocDbTemplate>DBInstancePrimaryIdentifier}} | 1         |
    Then assert metrics for all alarms are populated
    And sleep for "30" seconds
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 180 seconds, check every 15 seconds

  Scenario: To detect low values of CPUCreditBalance - red
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                    | ResourceType | KmsKey                              |
      | resource_manager/cloud_formation_templates/shared/KMS.yml          | SHARED       |                                     |
      | resource_manager/cloud_formation_templates/DocDbTemplate.yml       | ON_DEMAND    | {{cfn-output:KMS>EncryptAtRestKey}} |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml | SHARED       |                                     |
    When alarm "docdb:alarm:health-cpu_credit_balance:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | DBInstanceIdentifier                                     | Threshold |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:DocDbTemplate>DBInstancePrimaryIdentifier}} | 100       |
    Then assert metrics for all alarms are populated
    And sleep for "30" seconds
    And wait until alarm {{alarm:under_test>AlarmName}} becomes ALARM within 180 seconds, check every 15 seconds
