@ecs
Feature: SSM automation document Digito-ScaleService_2020-04-01

  Scenario: Execute SSM automation document Digito-ScaleService_2020-04-01 on Fargate. NewTaskDefinition. NumberOfTasks.
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                       | ResourceType | VPC                      |  PublicSubnetOne                    | PublicSubnetTwo                    |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                             | SHARED       |                          |                                     |                                    |
      | resource_manager/cloud_formation_templates/ECSFargateTemplate.yml                     | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>PublicSubnetOne}}  | {{cfn-output:VPC>PublicSubnetTwo}} |
      | documents/ecs/sop/scale_service/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                          |                                     |                                    |
    And published "Digito-ScaleService_2020-04-01" SSM document
    And create new task definition and cache it as "NewTaskDefinitionArn" "before" SSM automation execution
      | TaskDefinitionArn                                   | ClusterName                                   | ServiceName                                  |
      | {{cfn-output:ECSFargateTemplate>ECSTaskDefinition}} | {{cfn-output:ECSFargateTemplate>ClusterName}} | {{cfn-output:ECSFargateTemplate>ECSService}} |
    When SSM automation document "Digito-ScaleService_2020-04-01" executed
      | ClusterName                                   | ServiceName                                  | NewTaskDefinitionArn                   | NumberOfTasks | AutomationAssumeRole                                                       |
      | {{cfn-output:ECSFargateTemplate>ClusterName}} | {{cfn-output:ECSFargateTemplate>ECSService}} | {{cache:before>NewTaskDefinitionArn}}  |  2             | {{cfn-output:AutomationAssumeRoleTemplate>DigitoEcsScaleServiceAssumeRole}} |
    Then SSM automation document "Digito-ScaleService_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And waits until the ECSService is stable (tasks started or stopped)
      | ECSService                                    | ECSCluster                                    |
      | {{cfn-output:ECSFargateTemplate>ECSService}}  | {{cfn-output:ECSFargateTemplate>ClusterName}} |
    And cache number of tasks as "AmountOFTasks" "after" SSM execution
      | ECSService                                    | ECSCluster                                    |
      | {{cfn-output:ECSFargateTemplate>ECSService}}  | {{cfn-output:ECSFargateTemplate>ClusterName}} |
    And assert "AmountOFTasks" at "after" became equal to "2"


  Scenario: Execute SSM automation document Digito-ScaleService_2020-04-01 on Fargate. NewTaskDefinition. No NumberOfTasks.
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                       | ResourceType | VPC                      |  PublicSubnetOne                    | PublicSubnetTwo                    |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                             | SHARED       |                          |                                     |                                    |
      | resource_manager/cloud_formation_templates/ECSFargateTemplate.yml                     | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>PublicSubnetOne}}  | {{cfn-output:VPC>PublicSubnetTwo}} |
      | documents/ecs/sop/scale_service/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                          |                                     |                                    |
    And published "Digito-ScaleService_2020-04-01" SSM document
    And cache number of tasks as "AmountOFTasks" "before" SSM execution
      | ECSService                                    | ECSCluster                                    |
      | {{cfn-output:ECSFargateTemplate>ECSService}}  | {{cfn-output:ECSFargateTemplate>ClusterName}} |
    And create new task definition and cache it as "NewTaskDefinitionArn" "before" SSM automation execution
      | TaskDefinitionArn                                   | ClusterName                                   | ServiceName                                  |
      | {{cfn-output:ECSFargateTemplate>ECSTaskDefinition}} | {{cfn-output:ECSFargateTemplate>ClusterName}} | {{cfn-output:ECSFargateTemplate>ECSService}} |
    When SSM automation document "Digito-ScaleService_2020-04-01" executed
      | ClusterName                                   | ServiceName                                  | NewTaskDefinitionArn                   | AutomationAssumeRole                                                       |
      | {{cfn-output:ECSFargateTemplate>ClusterName}} | {{cfn-output:ECSFargateTemplate>ECSService}} | {{cache:before>NewTaskDefinitionArn}}  | {{cfn-output:AutomationAssumeRoleTemplate>DigitoEcsScaleServiceAssumeRole}} |
    Then SSM automation document "Digito-ScaleService_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And waits until the ECSService is stable (tasks started or stopped)
      | ECSService                                    | ECSCluster                                    |
      | {{cfn-output:ECSFargateTemplate>ECSService}}  | {{cfn-output:ECSFargateTemplate>ClusterName}} |
    And cache number of tasks as "AmountOFTasks" "after" SSM execution
      | ECSService                                    | ECSCluster                                    |
      | {{cfn-output:ECSFargateTemplate>ECSService}}  | {{cfn-output:ECSFargateTemplate>ClusterName}} |
    And assert "AmountOFTasks" at "before" became equal to "AmountOFTasks" at "after"


  Scenario: Execute SSM automation document Digito-ScaleService_2020-04-01 on Fargate. No NewTaskDefinition. No NumberOfTasks.
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                       | ResourceType | VPC                      |  PublicSubnetOne                    | PublicSubnetTwo                    |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                             | SHARED       |                          |                                     |                                    |
      | resource_manager/cloud_formation_templates/ECSFargateTemplate.yml                     | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>PublicSubnetOne}}  | {{cfn-output:VPC>PublicSubnetTwo}} |
      | documents/ecs/sop/scale_service/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                          |                                     |                                    |
    And published "Digito-ScaleService_2020-04-01" SSM document
    And cache number of tasks as "AmountOFTasks" "before" SSM execution
      | ECSService                                    | ECSCluster                                    |
      | {{cfn-output:ECSFargateTemplate>ECSService}}  | {{cfn-output:ECSFargateTemplate>ClusterName}} |
    When SSM automation document "Digito-ScaleService_2020-04-01" executed
      | ClusterName                                   | ServiceName                                   | AutomationAssumeRole                                                        |
      | {{cfn-output:ECSFargateTemplate>ClusterName}} | {{cfn-output:ECSFargateTemplate>ECSService}}  | {{cfn-output:AutomationAssumeRoleTemplate>DigitoEcsScaleServiceAssumeRole}} |
    Then SSM automation document "Digito-ScaleService_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And waits until the ECSService is stable (tasks started or stopped)
      | ECSService                                    | ECSCluster                                    |
      | {{cfn-output:ECSFargateTemplate>ECSService}}  | {{cfn-output:ECSFargateTemplate>ClusterName}} |
    And cache number of tasks as "AmountOFTasks" "after" SSM execution
      | ECSService                                    | ECSCluster                                    |
      | {{cfn-output:ECSFargateTemplate>ECSService}}  | {{cfn-output:ECSFargateTemplate>ClusterName}} |
    And assert "AmountOFTasks" at "before" became equal to "AmountOFTasks" at "after"


  Scenario: Execute SSM automation document Digito-ScaleService_2020-04-01 on Fargate. No NewTaskDefinition. NumberOfTasks.
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                       | ResourceType | VPC                      |  PublicSubnetOne                    | PublicSubnetTwo                    |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                             | SHARED       |                          |                                     |                                    |
      | resource_manager/cloud_formation_templates/ECSFargateTemplate.yml                     | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>PublicSubnetOne}}  | {{cfn-output:VPC>PublicSubnetTwo}} |
      | documents/ecs/sop/scale_service/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                          |                                     |                                    |
    And published "Digito-ScaleService_2020-04-01" SSM document
    And create new task definition and cache it as "NewTaskDefinitionArn" "before" SSM automation execution
      | TaskDefinitionArn                                   | ClusterName                                   | ServiceName                              |
      | {{cfn-output:ECSFargateTemplate>ECSTaskDefinition}} | {{cfn-output:ECSFargateTemplate>ClusterName}} | {{cfn-output:ECSFargateTemplate>ECSService}} |
    When SSM automation document "Digito-ScaleService_2020-04-01" executed
      | ClusterName                                   | ServiceName                                  | NumberOfTasks | AutomationAssumeRole                                                        |
      | {{cfn-output:ECSFargateTemplate>ClusterName}} | {{cfn-output:ECSFargateTemplate>ECSService}} |  2            | {{cfn-output:AutomationAssumeRoleTemplate>DigitoEcsScaleServiceAssumeRole}} |
    Then SSM automation document "Digito-ScaleService_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And waits until the ECSService is stable (tasks started or stopped)
      | ECSService                                    | ECSCluster                                    |
      | {{cfn-output:ECSFargateTemplate>ECSService}}  | {{cfn-output:ECSFargateTemplate>ClusterName}} |
    And cache number of tasks as "AmountOFTasks" "after" SSM execution
      | ECSService                                    | ECSCluster                                    |
      | {{cfn-output:ECSFargateTemplate>ECSService}}  | {{cfn-output:ECSFargateTemplate>ClusterName}} |
    And assert "AmountOFTasks" at "after" became equal to "2"


  Scenario: Execute SSM automation document Digito-ScaleService_2020-04-01 on Fargate. No NewTaskDefinition. Memory and CPU.
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                       | ResourceType | VPC                      |  PublicSubnetOne                    | PublicSubnetTwo                    |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                             | SHARED       |                          |                                     |                                    |
      | resource_manager/cloud_formation_templates/ECSFargateTemplate.yml                     | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>PublicSubnetOne}}  | {{cfn-output:VPC>PublicSubnetTwo}} |
      | documents/ecs/sop/scale_service/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                          |                                     |                                    |
    And published "Digito-ScaleService_2020-04-01" SSM document
    When SSM automation document "Digito-ScaleService_2020-04-01" executed
      | ClusterName                               | ServiceName                                      | TaskDefinitionCPU | TaskDefinitionRAM  | AutomationAssumeRole                                                        |
      | {{cfn-output:ECSFargateTemplate>ClusterName}} | {{cfn-output:ECSFargateTemplate>ECSService}} | 256               |  512               | {{cfn-output:AutomationAssumeRoleTemplate>DigitoEcsScaleServiceAssumeRole}} |
    Then SSM automation document "Digito-ScaleService_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And waits until the ECSService is stable (tasks started or stopped)
      | ECSService                                    | ECSCluster                                    |
      | {{cfn-output:ECSFargateTemplate>ECSService}}  | {{cfn-output:ECSFargateTemplate>ClusterName}} |
    And cache memory and cpu as "ContainerDefinitions" "after" SSM execution
      | TaskDefinitionArn                                   |
      | {{cfn-output:ECSFargateTemplate>ECSTaskDefinition}} |
    And assert "ContainerDefinitions" at "after" became equal to CPU and Memory
      |  TaskDefinitionCPU  | TaskDefinitionRAM  |
      |  256                | 512                |
