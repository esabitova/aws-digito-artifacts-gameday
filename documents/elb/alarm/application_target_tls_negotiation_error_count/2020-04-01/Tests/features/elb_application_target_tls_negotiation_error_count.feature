@elb @integration @alarm
Feature: Alarm Setup - application elastic load-balancer TargetTLSNegotiationErrorCount

  Scenario: Create elb:alarm:application_target_tls_negotiation_error_count:2020-04-01 based on TargetTLSNegotiationErrorCount metric and check OK status
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                | ResourceType | VPC                      | Subnet1                                            | Subnet2                                            | Subnet3                                              | EC2Subnet                                      | VPCCidr                    |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                      | SHARED       |                          |                                                    |                                                    |                                                      |                                                |                            |
      | resource_manager/cloud_formation_templates/ApplicationLoadBalancerTemplate.yml | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetOne}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetTwo}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetThree}} | {{cfn-output:VPC>PrivateSubnetWithInternet01}} | {{cfn-output:VPC>VPCCidr}} |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml             | SHARED       |                          |                                                    |                                                    |                                                      |                                                |                            |

    When alarm "elb:alarm:application_target_tls_negotiation_error_count:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | ApplicationELBArn                                                     | Threshold | MaxTimeMinutes |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:ApplicationLoadBalancerTemplate>ApplicationELBFullName}} | 1000      | 1              |
    And invoke lambda "{{cfn-output:ApplicationLoadBalancerTemplate>ProxyLambdaArn}}" with parameters
      | host             | {{cfn-output:ApplicationLoadBalancerTemplate>ApplicationELBUrl}} |
      | path             | /target_tls_negotiation_error                                    |
      | schema           | http                                                             |
      | request_count    | 3                                                                |
      | request_interval | 1                                                                |
    And sleep for "20" seconds
    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 180 seconds, check every 15 seconds

  Scenario: Create elb:alarm:application_target_tls_negotiation_error_count:2020-04-01 based on TargetTLSNegotiationErrorCount metric and check ALARM status
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                | ResourceType | VPC                      | Subnet1                                            | Subnet2                                            | Subnet3                                              | EC2Subnet                                      | VPCCidr                    |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                      | SHARED       |                          |                                                    |                                                    |                                                      |                                                |                            |
      | resource_manager/cloud_formation_templates/ApplicationLoadBalancerTemplate.yml | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetOne}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetTwo}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetThree}} | {{cfn-output:VPC>PrivateSubnetWithInternet01}} | {{cfn-output:VPC>VPCCidr}} |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml             | SHARED       |                          |                                                    |                                                    |                                                      |                                                |                            |

    When alarm "elb:alarm:application_target_tls_negotiation_error_count:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | ApplicationELBArn                                                     | Threshold | MaxTimeMinutes |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:ApplicationLoadBalancerTemplate>ApplicationELBFullName}} | 1         | 1              |
    And invoke lambda "{{cfn-output:ApplicationLoadBalancerTemplate>ProxyLambdaArn}}" with parameters
      | host             | {{cfn-output:ApplicationLoadBalancerTemplate>ApplicationELBUrl}} |
      | path             | /target_tls_negotiation_error                                    |
      | schema           | http                                                             |
      | request_count    | 3                                                                |
      | request_interval | 1                                                                |
    And sleep for "20" seconds
    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes ALARM within 180 seconds, check every 15 seconds
