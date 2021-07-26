@elb
Feature: SSM automation document Digito-ApplicationLbNetworkUnavailable_2020-04-01

  Scenario: Create Application Load Balancer and execute SSM automation
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                             | ResourceType | VPC                      | PrivateSubnet                                   |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                                                   | SHARED       |                          |                                                 |
      | resource_manager/cloud_formation_templates/ApplicationLoadBalancerTemplate.yml                              | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>PrivateSubnetWithoutInternet}} |
      | documents/elb/test/application_lb_network_unavailable/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                          |                                                 |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml                                          | SHARED       |                          |                                                 |

    And published "Digito-ApplicationLbNetworkUnavailable_2020-04-01" SSM document
    And alarm "elb:alarm:application_unhealthy_host_count:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | ApplicationELBArn                                             | Threshold | MaxTimeMinutes
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:ApplicationLoadBalancerTemplate>ApplicationELB}} | 1         | 1

    When SSM automation document "Digito-ApplicationLbNetworkUnavailable_2020-04-01" executed in status "Success"
      | LoadBalancerArn                                      | AutomationAssumeRole                                                                                    | SyntheticAlarmName                              |
      | {{cfn-output:ApplicationELBTemplate>LoadBalancerArn} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoLoadBalancerApplicationLbNetworkUnavailableAssumeRole}} | {{cfn-output:ApplicationLoadBalancerTemplate>AlwaysOKAlarm}} |

    Then SSM automation document "Digito-ApplicationLbNetworkUnavailable_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    # Add any post-execution caching and validation here