@elb
Feature: SSM automation document Digito-ApplicationLbNetworkUnavailable_2020-04-01

  Scenario: Execute SSM automation document Digito-ApplicationLbNetworkUnavailable_2020-04-01 to test failure case
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                             | ResourceType | VPC                      | Subnet1                                            | Subnet2                                            | Subnet3                                              | EC2Subnet                                      | VPCCidr                    |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                                                   | SHARED       |                          |                                                    |                                                    |                                                      |                                                |                            |
      | resource_manager/cloud_formation_templates/shared/CommonAlarms.yml                                          | SHARED       |                          |                                                    |                                                    |                                                      |                                                |                            |
      | resource_manager/cloud_formation_templates/ApplicationLoadBalancerTemplate.yml                              | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetOne}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetTwo}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetThree}} | {{cfn-output:VPC>PrivateSubnetWithInternet01}} | {{cfn-output:VPC>VPCCidr}} |
      | documents/elb/test/application_lb_network_unavailable/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                          |                                                    |                                                    |                                                      |                                                |                            |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml                                          | SHARED       |                          |                                                    |                                                    |                                                      |                                                |                            |
    And published "Digito-ApplicationLbNetworkUnavailable_2020-04-01" SSM document

    When SSM automation document "Digito-ApplicationLbNetworkUnavailable_2020-04-01" executed
      | LoadBalancerArn                                                  | AutomationAssumeRole                                                                                    | SyntheticAlarmName                            |
      | {{cfn-output:ApplicationLoadBalancerTemplate>ApplicationELBArn}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoLoadBalancerApplicationLbNetworkUnavailableAssumeRole}} | {{cfn-output:CommonAlarms>AlwaysOKAlarmName}} |
    And Wait for the SSM automation document "Digito-ApplicationLbNetworkUnavailable_2020-04-01" execution is on step "AssertAlarmToBeRed" in status "TimedOut" for "1000" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    Then Wait for the SSM automation document "Digito-ApplicationLbNetworkUnavailable_2020-04-01" execution is on step "AssertAlarmToBeGreen" in status "Success" for "1000" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And SSM automation document "Digito-ApplicationLbNetworkUnavailable_2020-04-01" execution in status "TimedOut"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

  Scenario: Execute SSM automation document Digito-ApplicationLbNetworkUnavailable_2020-04-01 with SecurityGroupIdsToDelete param specified to test failure case
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                             | ResourceType | VPC                      | Subnet1                                            | Subnet2                                            | Subnet3                                              | EC2Subnet                                      | VPCCidr                    |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                                                   | SHARED       |                          |                                                    |                                                    |                                                      |                                                |                            |
      | resource_manager/cloud_formation_templates/shared/CommonAlarms.yml                                          | SHARED       |                          |                                                    |                                                    |                                                      |                                                |                            |
      | resource_manager/cloud_formation_templates/ApplicationLoadBalancerTemplate.yml                              | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetOne}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetTwo}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetThree}} | {{cfn-output:VPC>PrivateSubnetWithInternet01}} | {{cfn-output:VPC>VPCCidr}} |
      | documents/elb/test/application_lb_network_unavailable/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                          |                                                    |                                                    |                                                      |                                                |                            |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml                                          | SHARED       |                          |                                                    |                                                    |                                                      |                                                |                            |
    And published "Digito-ApplicationLbNetworkUnavailable_2020-04-01" SSM document

    When SSM automation document "Digito-ApplicationLbNetworkUnavailable_2020-04-01" executed
      | LoadBalancerArn                                                  | AutomationAssumeRole                                                                                    | SyntheticAlarmName                            | SecurityGroupIdsToDelete                                                 |
      | {{cfn-output:ApplicationLoadBalancerTemplate>ApplicationELBArn}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoLoadBalancerApplicationLbNetworkUnavailableAssumeRole}} | {{cfn-output:CommonAlarms>AlwaysOKAlarmName}} | {{cfn-output:ApplicationLoadBalancerTemplate>LoadBalancerSecurityGroup}} |
    And Wait for the SSM automation document "Digito-ApplicationLbNetworkUnavailable_2020-04-01" execution is on step "AssertAlarmToBeRed" in status "TimedOut" for "1000" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    Then Wait for the SSM automation document "Digito-ApplicationLbNetworkUnavailable_2020-04-01" execution is on step "AssertAlarmToBeGreen" in status "Success" for "1000" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And SSM automation document "Digito-ApplicationLbNetworkUnavailable_2020-04-01" execution in status "TimedOut"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

