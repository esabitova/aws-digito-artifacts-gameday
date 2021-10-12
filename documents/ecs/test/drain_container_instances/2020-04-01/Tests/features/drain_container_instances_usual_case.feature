@ecs
Feature: SSM automation document Digito-DrainECSContainerInstancesTest_2020-04-01

  Scenario: Execute SSM automation document Digito-DrainECSContainerInstancesTest_2020-04-01
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                     | ResourceType | VPC                      | PublicSubnetOne                     | PublicSubnetTwo                    | DesiredCapacity | ServiceDesiredCount |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                                           | SHARED       |                          |                                     |                                    |                 |                     |
      | resource_manager/cloud_formation_templates/ECSEC2Template.yml                                       | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>PublicSubnetOne}}  | {{cfn-output:VPC>PublicSubnetTwo}} | 5               | 5                   |
      | documents/ecs/test/drain_container_instances/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml  | ASSUME_ROLE  |                          |                                     |                                    |                 |                     |
    And published "Digito-DrainECSContainerInstancesTest_2020-04-01" SSM document
    And cache number of tasks as "AmountOfTasks" "before" SSM execution
      | ECSService                                | ECSCluster                                |
      | {{cfn-output:ECSEC2Template>ECSService}}  | {{cfn-output:ECSEC2Template>ClusterName}} |
    And cache number of nodes in "ACTIVE" status as "AmountOfHealthyNodes" "before" SSM execution
      | ECSCluster                                |
      | {{cfn-output:ECSEC2Template>ClusterName}} |

    When SSM automation document "Digito-DrainECSContainerInstancesTest_2020-04-01" executed
      | ClusterName                               | AutomationAssumeRole                                                                   | ServiceHealthAlarmName                           |
      | {{cfn-output:ECSEC2Template>ClusterName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoEcsDrainContainerInstancesAssumeRole}} | {{cfn-output:ECSEC2Template>ECSTaskAmountAlarm}} |

    Then SSM automation document "Digito-DrainECSContainerInstancesTest_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache execution output value of "CreateTemplate.FISExperimentTemplateId" as "FISExperimentTemplateId" after SSM automation execution
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|
    And assert "CheckIsRollback,AssertAlarmToBeGreenBeforeTest,CreateTemplate,SleepForOneSecond,StartExperiment,AssertAlarmToBeRed,WaitForServiceToBeRestored,WaitExperiment,AssertExperimentCompleted,AssertAlarmToBeGreen,DeleteTemplate" steps are successfully executed in order
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache number of tasks as "AmountOfTasks" "after" SSM execution
      | ECSService                                | ECSCluster                                |
      | {{cfn-output:ECSEC2Template>ECSService}}  | {{cfn-output:ECSEC2Template>ClusterName}} |
    And cache number of nodes in "ACTIVE" status as "AmountOfHealthyNodes" "after" SSM execution
      | ECSCluster                                |
      | {{cfn-output:ECSEC2Template>ClusterName}} |
    And assert fis experiment template with id "{{cache:after>FISExperimentTemplateId}}" does not exist
    And assert "AmountOfTasks" at "before" became equal to "AmountOfTasks" at "after"
    And assert "AmountOfHealthyNodes" at "before" became equal to "AmountOfHealthyNodes" at "after"