@ecs
Feature: SSM automation document Digito-ForceECSServiceTaskFailureTest_2020-04-01

  Scenario: Execute SSM automation document Digito-ForceECSServiceTaskFailureTest_2020-04-01
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                               | ResourceType | VPC                      |  PublicSubnetOne                    | PublicSubnetTwo                    |ServiceDesiredCount |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                                     | SHARED       |                          |                                     |                                    |                    |
      | resource_manager/cloud_formation_templates/ECSEC2Template.yml                                 | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>PublicSubnetOne}}  | {{cfn-output:VPC>PublicSubnetTwo}} | 7                  |
      | documents/ecs/test/service_task_failure/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                          |                                     |                                    |                    |
    And published "Digito-ForceECSServiceTaskFailureTest_2020-04-01" SSM document
    And cache number of tasks as "AmountOfTasks" "before" SSM execution
      | ECSService                                | ECSCluster                                |
      | {{cfn-output:ECSEC2Template>ECSService}}  | {{cfn-output:ECSEC2Template>ClusterName}} |

    When SSM automation document "Digito-ForceECSServiceTaskFailureTest_2020-04-01" executed
      | ClusterName                               | ServiceName                                   | PercentageOfTasksToStop  | SyntheticAlarmName                               | AutomationAssumeRole                                                              |
      | {{cfn-output:ECSEC2Template>ClusterName}} | {{cfn-output:ECSEC2Template>ECSService}}      | 50                       | {{cfn-output:ECSEC2Template>ECSTaskAmountAlarm}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoForceECSServiceTaskFailureTestAssumeRole}} |
    Then SSM automation document "Digito-ForceECSServiceTaskFailureTest_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And assert "AssertAlarmToBeGreenBeforeTest,InjectFailure,StopSelectedTasks,WaitTasksToBeRestored,AssertAlarmToBeGreen" steps are successfully executed in order
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    And cache number of tasks as "AmountOfTasks" "after" SSM execution
      | ECSService                                | ECSCluster                                |
      | {{cfn-output:ECSEC2Template>ECSService}}  | {{cfn-output:ECSEC2Template>ClusterName}} |
    And assert "AmountOfTasks" at "before" became equal to "AmountOfTasks" at "after"
