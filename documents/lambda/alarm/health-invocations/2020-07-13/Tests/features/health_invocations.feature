@lambda @integration @alarm
Feature: Alarm Setup - Lambda Invocations
  Scenario: Test alarm lambda:alarm:health-invocations:2020-04-01
    Given the cloud formation templates as integration test resources
      |CfnTemplatePath                                                          |ResourceType |
      | resource_manager/cloud_formation_templates/LambdaTemplate.yml           | ON_DEMAND   |
      |resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml       | SHARED      |
    When alarm "lambda:alarm:health-invocations:2020-07-13" is installed
      |alarmId    |FunctionName                                 | Threshold | SNSTopicARN
      |under_test |{{cfn-output:LambdaTemplate>LambdaFunction}} |   1       | {{cfn-output:SnsForAlarms>Topic}}
    Then assert metrics for all alarms are populated

