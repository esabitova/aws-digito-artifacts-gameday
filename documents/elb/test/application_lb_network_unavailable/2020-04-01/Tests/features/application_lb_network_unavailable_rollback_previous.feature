@elb
Feature: SSM automation document Digito-ForceApplicationLbNetworkUnavailableTest_2020-04-01

  Scenario: Execute SSM automation document Digito-ForceApplicationLbNetworkUnavailableTest_2020-04-01 in rollback
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                             | ResourceType | VPC                      | Subnet1                                            | Subnet2                                            | Subnet3                                              | EC2Subnet                                      | VPCCidr                    |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                                                   | SHARED       |                          |                                                    |                                                    |                                                      |                                                |                            |
      | resource_manager/cloud_formation_templates/shared/CommonAlarms.yml                                          | SHARED       |                          |                                                    |                                                    |                                                      |                                                |                            |
      | resource_manager/cloud_formation_templates/ApplicationLoadBalancerTemplate.yml                              | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetOne}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetTwo}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetThree}} | {{cfn-output:VPC>PrivateSubnetWithInternet01}} | {{cfn-output:VPC>VPCCidr}} |
      | documents/elb/test/application_lb_network_unavailable/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                          |                                                    |                                                    |                                                      |                                                |                            |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml                                          | SHARED       |                          |                                                    |                                                    |                                                      |                                                |                            |
    And published "Digito-ForceApplicationLbNetworkUnavailableTest_2020-04-01" SSM document
    And cache load balancer security groups as "SecurityGroupsBefore" "before" SSM automation execution
      | LoadBalancerArn                                                  |
      | {{cfn-output:ApplicationLoadBalancerTemplate>ApplicationELBArn}} |

    When SSM automation document "Digito-ForceApplicationLbNetworkUnavailableTest_2020-04-01" executed
      | LoadBalancerArn                                                  | AutomationAssumeRole                                                                                 | SyntheticAlarmName                            | SecurityGroupIdsToDelete                                                 |
      | {{cfn-output:ApplicationLoadBalancerTemplate>ApplicationELBArn}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoForceApplicationLbNetworkUnavailableTestAssumeRole}} | {{cfn-output:CommonAlarms>AlwaysOKAlarmName}} | {{cfn-output:ApplicationLoadBalancerTemplate>LoadBalancerSecurityGroup}} |
    And Wait for the SSM automation document "Digito-ForceApplicationLbNetworkUnavailableTest_2020-04-01" execution is on step "AssertAlarmToBeRed" in status "InProgress" for "600" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And terminate "Digito-ForceApplicationLbNetworkUnavailableTest_2020-04-01" SSM automation document
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    Then Wait for the SSM automation document "Digito-ForceApplicationLbNetworkUnavailableTest_2020-04-01" execution is on step "TriggerRollback" in status "Success" for "240" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And SSM automation document "Digito-ForceApplicationLbNetworkUnavailableTest_2020-04-01" execution in status "Cancelled"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache rollback execution id
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And SSM automation document "Digito-ForceApplicationLbNetworkUnavailableTest_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>2}} |
    And assert "CheckIsRollback, GetInputsFromPreviousExecution, GetBackedUpSecurityGroupsFromPreviousExecution, AssertLoadBalancerArn, RollbackPreviousExecution" steps are successfully executed in order
      | ExecutionId                |
      | {{cache:SsmExecutionId>2}} |
    And cache load balancer security groups as "SecurityGroupsAfter" "after" SSM automation execution
      | LoadBalancerArn                                                  |
      | {{cfn-output:ApplicationLoadBalancerTemplate>ApplicationELBArn}} |
    And assert "SecurityGroupsBefore" at "before" became equal to "SecurityGroupsAfter" at "after"
