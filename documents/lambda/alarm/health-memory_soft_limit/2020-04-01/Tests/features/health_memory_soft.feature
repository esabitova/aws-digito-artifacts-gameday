@lambda @integration @alarm
Feature: Alarm Setup - Memory Soft Limit
  Scenario: Test alarm lambda:alarm:health-memory_soft_limit:2020-04-01
    Given the cloud formation templates as integration test resources
      |CfnTemplatePath                                                          |ResourceType |
      | resource_manager/cloud_formation_templates/LambdaTemplate.yml           | ON_DEMAND   |
      |resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml       | SHARED      |
    When alarm "lambda:alarm:health-memory_soft_limit:2020-04-01" is installed
      |alarmId    |FunctionName                                 | Threshold   | SNSTopicARN
      |under_test |{{cfn-output:LambdaTemplate>LambdaFunction}} |  2000       | {{cfn-output:SnsForAlarms>Topic}} 
    And invoke ordinary function "400" times
      | LambdaARN                               |
      | {{cfn-output:LambdaTemplate>LambdaARN}} |
    Then assert metrics for all alarms are populated within 1200 seconds, check every 60 seconds
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 300 seconds, check every 30 seconds
