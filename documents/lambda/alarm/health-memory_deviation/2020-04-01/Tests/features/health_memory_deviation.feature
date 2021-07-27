@lambda @integration @alarm
Feature: Alarm Setup - Lambda Average Memory Growth
  Scenario: Test alarm lambda:alarm:health-memory_deviation:2020-04-01
    Given the cloud formation templates as integration test resources
      |CfnTemplatePath                                                          |ResourceType |
      | resource_manager/cloud_formation_templates/LambdaTemplate.yml           | ON_DEMAND   |
      |resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml       | SHARED      |
    When alarm "lambda:alarm:health-memory_deviation:2020-04-01" is installed
      |alarmId    |FunctionName                                 | Threshold | SNSTopicARN
      |under_test |{{cfn-output:LambdaTemplate>LambdaFunction}} |   1       | {{cfn-output:SnsForAlarms>Topic}}
    And invoke ordinary function "400" times
      | LambdaARN                               |
      | {{cfn-output:LambdaTemplate>LambdaARN}} |
    Then assert metrics for all alarms are populated within 2400 seconds, check every 60 seconds
