@elb
Feature: SSM automation document Digito-NetworkGwLbTargetUnavailable_2020-04-01

  Scenario: Create Network LB and execute automation
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                           | ResourceType |  VPC                     | PrivateSubnet                                   |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                                                 | SHARED       |                          |                                                 |
      | resource_manager/cloud_formation_templates/NetworkLoadBalancerTemplate.yml                                | ON_DEMAND    | {{cfn-output:VPC>VPCId}} |{{cfn-output:VPC>PrivateSubnetWithoutInternet}}  |
      | documents/elb/test/network_gw_lb_target_unavailable/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                          |                                                 |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml                                        | SHARED       |                          |                                                 |
    And published "Digito-NetworkGwLbTargetUnavailable_2020-04-01" SSM document
    And alarm "elb:alarm:network_unhealthy_host_count:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | ApplicationELBArn                                     | Threshold  | MaxTimeMinutes
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:NetworkLoadBalancerTemplate>NetworkELB}} | 1          | 1
    When SSM automation document "Digito-NetworkGwLbTargetUnavailable_2020-04-01" executed
      | LoadBalancerArn                                       | SyntheticAlarmName             |  AutomationAssumeRole                                                                               |
      | {{cfn-output:NetworkLoadBalancerTemplate>NetworkELB}} | {{alarm:under_test>AlarmName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoLoadBalancerNetworkLbTargetUnavailableAssumeRole}} |

    Then SSM automation document "Digito-NetworkGwLbTargetUnavailable_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |


#  Scenario: Create Gateway LB and execute automation
#    Given the cloud formation templates as integration test resources
#      | CfnTemplatePath                                                                                                     | ResourceType |
#      | resource_manager/cloud_formation_templates/GatewayLoadBalancerTemplate.yml                                          | ON_DEMAND    |
#      | documents/elb/test/network_gw_lb_target_unavailable/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
#    And published "Digito-NetworkGwLbTargetUnavailable_2020-04-01" SSM document
#    # Add any pre-execution caching and setup steps here
#
#    When SSM automation document "Digito-NetworkGwLbTargetUnavailable_2020-04-01" executed
#      # Add other parameter names below
#      | LoadBalancerArn                                           | AutomationAssumeRole                                                                               | SyntheticAlarmName                               |
#      # Replace parameter values to point to the corresponding outputs in cloudformation template
#      | {{cfn-output:GatewayLoadBalancerTemplate>LoadBalancerArn} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoLoadBalancerNetworkLbTargetUnavailableAssumeRole}} | {{cfn-output:NetworkLoadBalancerTemplate>Alarm}} |
#    # Add other steps that should run parallel to the document here
#
#    Then SSM automation document "Digito-NetworkGwLbTargetUnavailable_2020-04-01" execution in status "Success"
#      | ExecutionId                |
#      | {{cache:SsmExecutionId>1}} |
## Add any post-execution caching and validation here