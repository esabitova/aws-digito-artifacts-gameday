@api-gw @integration @alarm
Feature: Alarm Setup - API Gateway Errors
  Scenario: Test API Gateway api-gw:alarm:health-latency:2020-04-01
    Given the cloud formation templates as integration test resources
      |CfnTemplatePath                                                          |ResourceType |
      | resource_manager/cloud_formation_templates/RestApiGwTemplate.yml        | ON_DEMAND   |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml      | SHARED      |
    And cache value of "ApiKeyId,ApiHost,ApiPath" "before" SSM automation execution
      | ApiKeyId                                  | ApiHost                                        | ApiPath                                             |
      | {{cfn-output:RestApiGwTemplate>ApiKeyId}} | {{cfn-output:RestApiGwTemplate>RestApiGwHost}} | {{cfn-output:RestApiGwTemplate>RestApiGwStagePath}} | 
    When alarm "api-gw:alarm:health-latency:2020-04-01" is installed
      | alarmId    | ApiName                                  | Threshold | SNSTopicARN                       |
      | under_test | {{cfn-output:RestApiGwTemplate>ApiName}} | 240       | {{cfn-output:SnsForAlarms>Topic}} |
    And get API key and perform "6" https "GET" requests with interval "10" seconds
    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 90 seconds, check every 15 seconds

