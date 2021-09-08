@ecs
Feature: SSM automation document Digito-DrainECSContainerInstancesTest_2020-04-01

  Scenario: Execute SSM automation document Digito-DrainECSContainerInstancesTest_2020-04-01 and rollback
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                     | ResourceType | VPC                      | PublicSubnetOne                     | PublicSubnetTwo                    | DesiredCapacity | ServiceDesiredCount |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                                           | SHARED       |                          |                                     |                                    |                 |                     |
      | resource_manager/cloud_formation_templates/ECSEC2Template.yml                                       | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>PublicSubnetOne}}  | {{cfn-output:VPC>PublicSubnetTwo}} | 5               | 5                   |
      | documents/ecs/test/drain_container_instances/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml  | ASSUME_ROLE  |                          |                                     |                                    |                 |                     |
    And published "Digito-DrainECSContainerInstancesTest_2020-04-01" SSM document
    When SSM automation document "Digito-DrainECSContainerInstancesTest_2020-04-01" executed
      | ClusterName                               | AutomationAssumeRole                                                                   | ServiceHealthAlarmName                           |
      | {{cfn-output:ECSEC2Template>ClusterName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoEcsDrainContainerInstancesAssumeRole}} | {{cfn-output:ECSEC2Template>ECSTaskAmountAlarm}} |

    Then Wait for the SSM automation document "Digito-DrainECSContainerInstancesTest_2020-04-01" execution is on step "AssertAlarmToBeRed" in status "InProgress"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And terminate "Digito-DrainECSContainerInstancesTest_2020-04-01" SSM automation document
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    And Wait for the SSM automation document "Digito-DrainECSContainerInstancesTest_2020-04-01" execution is on step "TriggerRollback" in status "Success"
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|
    And SSM automation document "Digito-DrainECSContainerInstancesTest_2020-04-01" execution in status "Cancelled"
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|
    And cache rollback execution id
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|
    And SSM automation document "Digito-DrainECSContainerInstancesTest_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>2}} |
