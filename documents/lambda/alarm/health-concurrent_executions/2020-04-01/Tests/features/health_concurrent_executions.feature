@lambda @integration @alarm
Feature: Alarm Setup - Lambda ConcurrentExecutions
  Scenario: Test alarm lambda:alarm:health-concurrent_executions:2020-04-01
    Given the cloud formation templates as integration test resources
      |CfnTemplatePath                                                          |ResourceType |
      | resource_manager/cloud_formation_templates/LambdaTemplate.yml           | ON_DEMAND   |
      |resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml       | SHARED      |
    When alarm "lambda:alarm:health-concurrent_executions:2020-04-01" is installed
      |alarmId    |FunctionName                                 | Threshold | SNSTopicARN
      |under_test |{{cfn-output:LambdaTemplate>LambdaFunction}} | 90        | {{cfn-output:SnsForAlarms>Topic}}
    And test lambda function under stress "300" seconds overall with "50" invokes in each test and "20" seconds delay
      | LambdaARN                               |
      | {{cfn-output:LambdaTemplate>LambdaARN}} |
    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 120 seconds, check every 15 seconds
