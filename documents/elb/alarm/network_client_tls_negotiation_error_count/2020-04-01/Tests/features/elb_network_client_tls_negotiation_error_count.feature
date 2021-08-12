@elb @integration @alarm
Feature: Alarm Setup - network load-balancer ClientTLSNegotiationErrorCount

  Scenario: Create elb:alarm:network_client_tls_negotiation_error_count:2020-04-01 based on ClientTLSNegotiationErrorCount metric normal case
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                | ResourceType | VPC                      | VPCCidr                    | Subnet1                                            | Subnet2                                            | Subnet3                                              |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                      | SHARED       |                          |                            |                                                    |                                                    |                                                      |
      | resource_manager/cloud_formation_templates/NetworkLoadBalancerTemplate.yml     | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>VPCCidr}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetOne}} |                                                    |                                                      |
      | resource_manager/cloud_formation_templates/ApplicationLoadBalancerTemplate.yml | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>VPCCidr}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetOne}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetTwo}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetThree}} |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml             | SHARED       |                          |                            |                                                    |                                                    |                                                      |
    When alarm "elb:alarm:network_client_tls_negotiation_error_count:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | NetworkLoadBalancerName                                              | Threshold | MaxTimeMinutes
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:NetworkLoadBalancerTemplate>NetworkELBFullName}} | 1000      | 1
    And invoke lambda "{{cfn-output:ApplicationLoadBalancerWithHttpsTemplate>ProxyLambdaArn}}" with parameters
      | host             | {{cfn-output:NetworkLoadBalancerTemplate>NetworkELBUrl}} |
      | path             | /                                                        |
      | schema           | https                                                    |
      | request_count    | 3                                                        |
      | request_interval | 1                                                        |
    And sleep for "20" seconds
    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 180 seconds, check every 15 seconds


