@elb
Feature: SSM automation document Digito-ApplicationLbNetworkUnavailable_2020-04-01

  Scenario: Execute SSM automation document Digito-ApplicationLbNetworkUnavailable_2020-04-01 usual case
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                             | ResourceType | VPC                      | Subnet1                                            | Subnet2                                            | Subnet3                                              | EC2Subnet                                      | VPCCidr                    |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                                                   | SHARED       |                          |                                                    |                                                    |                                                      |                                                |                            |
      | resource_manager/cloud_formation_templates/ApplicationLoadBalancerTemplate.yml                              | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetOne}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetTwo}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetThree}} | {{cfn-output:VPC>PrivateSubnetWithInternet01}} | {{cfn-output:VPC>VPCCidr}} |
      | documents/elb/test/application_lb_network_unavailable/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                          |                                                    |                                                    |                                                      |                                                |                            |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml                                          | SHARED       |                          |                                                    |                                                    |                                                      |                                                |                            |

    And published "Digito-ApplicationLbNetworkUnavailable_2020-04-01" SSM document
    And alarm "elb:alarm:application_unhealthy_host_count:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | ApplicationELBFullName                                                | LambdaTargetFullName                                                 | Threshold | EvaluationPeriods | DatapointsToAlarm |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:ApplicationLoadBalancerTemplate>ApplicationELBFullName}} | {{cfn-output:ApplicationLoadBalancerTemplate>HealthyTargetFullName}} | 1         | 1                 | 1                 |
    And cache load balancer security groups as "SecurityGroupsBefore" "before" SSM automation execution
      | LoadBalancerArn                                                  |
      | {{cfn-output:ApplicationLoadBalancerTemplate>ApplicationELBArn}} |

    When SSM automation document "Digito-ApplicationLbNetworkUnavailable_2020-04-01" executed
      | LoadBalancerArn                                                  | AutomationAssumeRole                                                                                    | SyntheticAlarmName             |
      | {{cfn-output:ApplicationLoadBalancerTemplate>ApplicationELBArn}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoLoadBalancerApplicationLbNetworkUnavailableAssumeRole}} | {{alarm:under_test>AlarmName}} |

    Then SSM automation document "Digito-ApplicationLbNetworkUnavailable_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And assert "CheckIsRollback, AssertAlarmToBeGreenBeforeTest, BackupCurrentExecution, GetVpcId, NumberOfSecurityGroupsIdsToDelete, CheckSecurityGroupIdsToDeleteParamIsNotEmpty, CreateEmptySecurityGroup, SetEmptySecurityGroupForLoadBalancer, AssertAlarmToBeRed, RollbackCurrentExecution, DeleteEmptySecurityGroupIfCreated, DeleteEmptySecurityGroup, AssertAlarmToBeGreen" steps are successfully executed in order
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache load balancer security groups as "SecurityGroupsAfter" "after" SSM automation execution
      | LoadBalancerArn                                                  |
      | {{cfn-output:ApplicationLoadBalancerTemplate>ApplicationELBArn}} |
    And assert "SecurityGroupsBefore" at "before" became equal to "SecurityGroupsAfter" at "after"

  Scenario: Execute SSM automation document Digito-ApplicationLbNetworkUnavailable_2020-04-01 with SecurityGroupIdsToDelete param specified
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                             | ResourceType | VPC                      | Subnet1                                            | Subnet2                                            | Subnet3                                              | EC2Subnet                                      | VPCCidr                    |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                                                   | SHARED       |                          |                                                    |                                                    |                                                      |                                                |                            |
      | resource_manager/cloud_formation_templates/ApplicationLoadBalancerTemplate.yml                              | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetOne}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetTwo}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetThree}} | {{cfn-output:VPC>PrivateSubnetWithInternet01}} | {{cfn-output:VPC>VPCCidr}} |
      | documents/elb/test/application_lb_network_unavailable/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                          |                                                    |                                                    |                                                      |                                                |                            |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml                                          | SHARED       |                          |                                                    |                                                    |                                                      |                                                |                            |

    And published "Digito-ApplicationLbNetworkUnavailable_2020-04-01" SSM document
    And alarm "elb:alarm:application_unhealthy_host_count:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | ApplicationELBFullName                                                | LambdaTargetFullName                                                 | Threshold | EvaluationPeriods | DatapointsToAlarm |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:ApplicationLoadBalancerTemplate>ApplicationELBFullName}} | {{cfn-output:ApplicationLoadBalancerTemplate>HealthyTargetFullName}} | 1         | 1                 | 1                 |
    And cache load balancer security groups as "SecurityGroupsBefore" "before" SSM automation execution
      | LoadBalancerArn                                                  |
      | {{cfn-output:ApplicationLoadBalancerTemplate>ApplicationELBArn}} |

    When SSM automation document "Digito-ApplicationLbNetworkUnavailable_2020-04-01" executed
      | LoadBalancerArn                                                  | AutomationAssumeRole                                                                                    | SyntheticAlarmName             | SecurityGroupIdsToDelete                                                 |
      | {{cfn-output:ApplicationLoadBalancerTemplate>ApplicationELBArn}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoLoadBalancerApplicationLbNetworkUnavailableAssumeRole}} | {{alarm:under_test>AlarmName}} | {{cfn-output:ApplicationLoadBalancerTemplate>LoadBalancerSecurityGroup}} |

    Then SSM automation document "Digito-ApplicationLbNetworkUnavailable_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And assert "CheckIsRollback, AssertAlarmToBeGreenBeforeTest, BackupCurrentExecution, GetVpcId, NumberOfSecurityGroupsIdsToDelete, CheckSecurityGroupIdsToDeleteParamIsNotEmpty, RemoveSecurityGroupsFromList, SetNewSecurityGroups, AssertAlarmToBeRed, RollbackCurrentExecution, DeleteEmptySecurityGroupIfCreated, AssertAlarmToBeGreen" steps are successfully executed in order
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache load balancer security groups as "SecurityGroupsAfter" "after" SSM automation execution
      | LoadBalancerArn                                                  |
      | {{cfn-output:ApplicationLoadBalancerTemplate>ApplicationELBArn}} |
    And assert "SecurityGroupsBefore" at "before" became equal to "SecurityGroupsAfter" at "after"
