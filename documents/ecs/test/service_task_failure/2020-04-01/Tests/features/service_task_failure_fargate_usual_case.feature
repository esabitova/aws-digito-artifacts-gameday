@ecs
Feature: SSM automation document Digito-ForceECSServiceTaskFailureTest_2020-04-01

  Scenario: Execute SSM automation document Digito-ForceECSServiceTaskFailureTest_2020-04-01
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                               | ResourceType | VPC                      |  PublicSubnetOne                    | PublicSubnetTwo                    |ServiceDesiredCount |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                                     | SHARED       |                          |                                     |                                    |                    |
      | resource_manager/cloud_formation_templates/ECSFargateTemplate.yml                             | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>PublicSubnetOne}}  | {{cfn-output:VPC>PublicSubnetTwo}} | 7                  |
      | documents/ecs/test/service_task_failure/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                          |                                     |                                    |                    |
    And published "Digito-ForceECSServiceTaskFailureTest_2020-04-01" SSM document
    And cache number of tasks as "AmountOfTasks" "before" SSM execution
      | ECSService                                    | ECSCluster                                    |
      | {{cfn-output:ECSFargateTemplate>ECSService}}  | {{cfn-output:ECSFargateTemplate>ClusterName}} |

    When SSM automation document "Digito-ForceECSServiceTaskFailureTest_2020-04-01" executed
      | ClusterName                                   | ServiceName                                       | PercentageOfTasksToStop  | SyntheticAlarmName                                          | AutomationAssumeRole                                                              |
      | {{cfn-output:ECSFargateTemplate>ClusterName}} | {{cfn-output:ECSFargateTemplate>ECSService}}      | 50                       | {{cfn-output:ECSFargateTemplate>ECSFargateTaskAmountAlarm}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoForceECSServiceTaskFailureTestAssumeRole}} |
    Then SSM automation document "Digito-ForceECSServiceTaskFailureTest_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And assert "AssertAlarmToBeGreenBeforeTest,InjectFailure,StopSelectedTasks,WaitForServiceToBeRestored,AssertAlarmToBeGreen" steps are successfully executed in order
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    And cache number of tasks as "AmountOfTasks" "after" SSM execution
      | ECSService                                    | ECSCluster                                    |
      | {{cfn-output:ECSFargateTemplate>ECSService}}  | {{cfn-output:ECSFargateTemplate>ClusterName}} |
    And assert "AmountOfTasks" at "before" became equal to "AmountOfTasks" at "after"