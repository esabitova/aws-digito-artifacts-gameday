@load-balancer
Feature: SSM automation document Digito-ForceApplicationLbNetworkUnavailableTest_2020-04-01

  Scenario: Execute SSM automation document Digito-ForceApplicationLbNetworkUnavailableTest_2020-04-01 to test failure case
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                             | ResourceType | VPC                      | Subnet1                                            | Subnet2                                            | Subnet3                                              | EC2Subnet                                      | VPCCidr                    |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                                                   | SHARED       |                          |                                                    |                                                    |                                                      |                                                |                            |
      | resource_manager/cloud_formation_templates/shared/CommonAlarms.yml                                          | SHARED       |                          |                                                    |                                                    |                                                      |                                                |                            |
      | resource_manager/cloud_formation_templates/ApplicationLoadBalancerTemplate.yml                              | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetOne}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetTwo}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetThree}} | {{cfn-output:VPC>PrivateSubnetWithInternet01}} | {{cfn-output:VPC>VPCCidr}} |
      | documents/load-balancer/test/application_lb_network_unavailable/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                          |                                                    |                                                    |                                                      |                                                |                            |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml                                          | SHARED       |                          |                                                    |                                                    |                                                      |                                                |                            |
    And published "Digito-ForceApplicationLbNetworkUnavailableTest_2020-04-01" SSM document
    And cache load balancer security groups as "SecurityGroupsBefore" "before" SSM automation execution
      | LoadBalancerArn                                                  |
      | {{cfn-output:ApplicationLoadBalancerTemplate>ApplicationELBArn}} |

    When SSM automation document "Digito-ForceApplicationLbNetworkUnavailableTest_2020-04-01" executed
      | LoadBalancerArn                                                  | AutomationAssumeRole                                                                                 | SyntheticAlarmName                            |
      | {{cfn-output:ApplicationLoadBalancerTemplate>ApplicationELBArn}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoForceApplicationLbNetworkUnavailableTestAssumeRole}} | {{cfn-output:CommonAlarms>AlwaysOKAlarmName}} |
    And Wait for the SSM automation document "Digito-ForceApplicationLbNetworkUnavailableTest_2020-04-01" execution is on step "AssertAlarmToBeRed" in status "TimedOut" for "1000" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    Then Wait for the SSM automation document "Digito-ForceApplicationLbNetworkUnavailableTest_2020-04-01" execution is on step "AssertAlarmToBeGreen" in status "Success" for "1000" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And SSM automation document "Digito-ForceApplicationLbNetworkUnavailableTest_2020-04-01" execution in status "TimedOut"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And assert "CheckIsRollback, AssertAlarmToBeGreenBeforeTest, BackupCurrentExecution, GetVpcId, NumberOfSecurityGroupsIdsToDelete, CheckSecurityGroupIdsToDeleteParamIsNotEmpty, CreateEmptySecurityGroup, SetEmptySecurityGroupForLoadBalancer, RollbackCurrentExecution, DeleteEmptySecurityGroupIfCreated, DeleteEmptySecurityGroup, AssertAlarmToBeGreen" steps are successfully executed in order
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache load balancer security groups as "SecurityGroupsAfter" "after" SSM automation execution
      | LoadBalancerArn                                                  |
      | {{cfn-output:ApplicationLoadBalancerTemplate>ApplicationELBArn}} |
    And assert "SecurityGroupsBefore" at "before" became equal to "SecurityGroupsAfter" at "after"

  Scenario: Execute SSM automation document Digito-ForceApplicationLbNetworkUnavailableTest_2020-04-01 with SecurityGroupIdsToDelete param specified to test failure case
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                             | ResourceType | VPC                      | Subnet1                                            | Subnet2                                            | Subnet3                                              | EC2Subnet                                      | VPCCidr                    |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                                                   | SHARED       |                          |                                                    |                                                    |                                                      |                                                |                            |
      | resource_manager/cloud_formation_templates/shared/CommonAlarms.yml                                          | SHARED       |                          |                                                    |                                                    |                                                      |                                                |                            |
      | resource_manager/cloud_formation_templates/ApplicationLoadBalancerTemplate.yml                              | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetOne}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetTwo}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetThree}} | {{cfn-output:VPC>PrivateSubnetWithInternet01}} | {{cfn-output:VPC>VPCCidr}} |
      | documents/load-balancer/test/application_lb_network_unavailable/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                          |                                                    |                                                    |                                                      |                                                |                            |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml                                          | SHARED       |                          |                                                    |                                                    |                                                      |                                                |                            |
    And published "Digito-ForceApplicationLbNetworkUnavailableTest_2020-04-01" SSM document
    And cache load balancer security groups as "SecurityGroupsBefore" "before" SSM automation execution
      | LoadBalancerArn                                                  |
      | {{cfn-output:ApplicationLoadBalancerTemplate>ApplicationELBArn}} |

    When SSM automation document "Digito-ForceApplicationLbNetworkUnavailableTest_2020-04-01" executed
      | LoadBalancerArn                                                  | AutomationAssumeRole                                                                                 | SyntheticAlarmName                            | SecurityGroupIdsToDelete                                                 |
      | {{cfn-output:ApplicationLoadBalancerTemplate>ApplicationELBArn}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoForceApplicationLbNetworkUnavailableTestAssumeRole}} | {{cfn-output:CommonAlarms>AlwaysOKAlarmName}} | {{cfn-output:ApplicationLoadBalancerTemplate>LoadBalancerSecurityGroup}} |
    And Wait for the SSM automation document "Digito-ForceApplicationLbNetworkUnavailableTest_2020-04-01" execution is on step "AssertAlarmToBeRed" in status "TimedOut" for "1000" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    Then Wait for the SSM automation document "Digito-ForceApplicationLbNetworkUnavailableTest_2020-04-01" execution is on step "AssertAlarmToBeGreen" in status "Success" for "1000" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And SSM automation document "Digito-ForceApplicationLbNetworkUnavailableTest_2020-04-01" execution in status "TimedOut"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And assert "CheckIsRollback, AssertAlarmToBeGreenBeforeTest, BackupCurrentExecution, GetVpcId, NumberOfSecurityGroupsIdsToDelete, CheckSecurityGroupIdsToDeleteParamIsNotEmpty, RemoveSecurityGroupsFromList, SetNewSecurityGroups, RollbackCurrentExecution, DeleteEmptySecurityGroupIfCreated, AssertAlarmToBeGreen" steps are successfully executed in order
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache load balancer security groups as "SecurityGroupsAfter" "after" SSM automation execution
      | LoadBalancerArn                                                  |
      | {{cfn-output:ApplicationLoadBalancerTemplate>ApplicationELBArn}} |
    And assert "SecurityGroupsBefore" at "before" became equal to "SecurityGroupsAfter" at "after"

