@elb @integration @alarm
Feature: Alarm Setup - application elastic load-balancer ClientTLSNegotiationErrorCount

  Scenario: Create elb:alarm:application_client_tls_negotiation_error_count:2020-04-01 based on ClientTLSNegotiationErrorCount metric normal case
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                | ResourceType | VPC                      | Subnet1                                            | Subnet2                                            | Subnet3                                              | VPCCidr                    |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                      | SHARED       |                          |                                                    |                                                    |                                                      |                            |
      | resource_manager/cloud_formation_templates/ApplicationLoadBalancerTemplate.yml | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetOne}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetTwo}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetThree}} | {{cfn-output:VPC>VPCCidr}} |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml             | SHARED       |                          |                                                    |                                                    |                                                      |                            |

    When alarm "elb:alarm:application_client_tls_negotiation_error_count:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | ApplicationELBArn                                                     | Threshold | MaxTimeMinutes |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:ApplicationLoadBalancerTemplate>ApplicationELBFullName}} | 1000      | 1              |
    And invoke lambda "{{cfn-output:ApplicationLoadBalancerTemplate>ProxyLambdaArn}}" with parameters
      | host             | {{cfn-output:ApplicationLoadBalancerTemplate>ApplicationELBUrl}} |
      | path             | /                                                                |
      | schema           | https                                                            |
      | request_count    | 3                                                                |
      | request_interval | 1                                                                |
    And sleep for "20" seconds
    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 180 seconds, check every 15 seconds

  Scenario: Create elb:alarm:application_client_tls_negotiation_error_count:2020-04-01 based on ClientTLSNegotiationErrorCount metric state.ALARM case
    Given the cached input parameters
      | ssl_certificate_arn                                                                 |
      | arn:aws:acm:eu-west-1:435978235099:certificate/bef22097-8526-498a-b30b-54bfc631559d |

    And the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                | ResourceType | VPC                      | Subnet1                                            | Subnet2                                            | Subnet3                                              | VPCCidr                    | SSLCertificateArn             |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                      | SHARED       |                          |                                                    |                                                    |                                                      |                            |                               |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml             | SHARED       |                          |                                                    |                                                    |                                                      |                            |                               |
      | resource_manager/cloud_formation_templates/ApplicationLoadBalancerTemplate.yml | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetOne}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetTwo}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetThree}} | {{cfn-output:VPC>VPCCidr}} | {{cache:ssl_certificate_arn}} |

    When alarm "elb:alarm:application_client_tls_negotiation_error_count:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | ApplicationELBArn                                                     | Threshold | MaxTimeMinutes |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:ApplicationLoadBalancerTemplate>ApplicationELBFullName}} | 1         | 1              |
    And invoke lambda "{{cfn-output:ApplicationLoadBalancerTemplate>ProxyLambdaArn}}" with parameters
      | host             | {{cfn-output:ApplicationLoadBalancerTemplate>ApplicationELBUrl}} |
      | path             | /                                                                |
      | schema           | https                                                            |
      | request_count    | 3                                                                |
      | request_interval | 1                                                                |
    And sleep for "20" seconds
    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes ALARM within 180 seconds, check every 15 seconds
