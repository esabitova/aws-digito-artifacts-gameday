@ecs
Feature: SSM automation document Digito-ScaleECSServiceSOP_2020-04-01

  Scenario: Execute SSM automation document Digito-ScaleECSServiceSOP_2020-04-01 on EC2. NewTaskDefinition. NumberOfTasks.
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                       | ResourceType | VPC                      |  PublicSubnetOne                    | PublicSubnetTwo                    |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                             | SHARED       |                          |                                     |                                    |
      | resource_manager/cloud_formation_templates/ECSEC2Template.yml                         | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>PublicSubnetOne}}  | {{cfn-output:VPC>PublicSubnetTwo}} |
      | documents/ecs/sop/scale_service/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                          |                                     |                                    |
    And published "Digito-ScaleECSServiceSOP_2020-04-01" SSM document
    And create new task definition and cache it as "NewTaskDefinitionArn" "before" SSM automation execution
      | TaskDefinitionArn                               | ClusterName                               | ServiceName                              |
      | {{cfn-output:ECSEC2Template>ECSTaskDefinition}} | {{cfn-output:ECSEC2Template>ClusterName}} | {{cfn-output:ECSEC2Template>ECSService}} |
    When SSM automation document "Digito-ScaleECSServiceSOP_2020-04-01" executed
      | ClusterName                               | ServiceName                              | NewTaskDefinitionArn                   | NumberOfTasks | AutomationAssumeRole                                                           |
      | {{cfn-output:ECSEC2Template>ClusterName}} | {{cfn-output:ECSEC2Template>ECSService}} | {{cache:before>NewTaskDefinitionArn}}  | 2             | {{cfn-output:AutomationAssumeRoleTemplate>DigitoScaleECSServiceSOPAssumeRole}} |
    Then SSM automation document "Digito-ScaleECSServiceSOP_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache number of tasks as "AmountOFTasks" "after" SSM execution
      | ECSService                                | ECSCluster                                |
      | {{cfn-output:ECSEC2Template>ECSService}}  | {{cfn-output:ECSEC2Template>ClusterName}} |
    And assert "AmountOFTasks" at "after" became equal to "2"


  Scenario: Execute SSM automation document Digito-ScaleECSServiceSOP_2020-04-01 on EC2. NewTaskDefinition. No NumberOfTasks.
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                       | ResourceType | VPC                      |  PublicSubnetOne                    | PublicSubnetTwo                    |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                             | SHARED       |                          |                                     |                                    |
      | resource_manager/cloud_formation_templates/ECSEC2Template.yml                         | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>PublicSubnetOne}}  | {{cfn-output:VPC>PublicSubnetTwo}} |
      | documents/ecs/sop/scale_service/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                          |                                     |                                    |
    And published "Digito-ScaleECSServiceSOP_2020-04-01" SSM document
    And waits until the ECSService is stable (tasks started or stopped)
      | ECSService                                | ECSCluster                                |
      | {{cfn-output:ECSEC2Template>ECSService}}  | {{cfn-output:ECSEC2Template>ClusterName}} |
    And cache number of tasks as "AmountOFTasks" "before" SSM execution
      | ECSService                                | ECSCluster                                |
      | {{cfn-output:ECSEC2Template>ECSService}}  | {{cfn-output:ECSEC2Template>ClusterName}} |
    And create new task definition and cache it as "NewTaskDefinitionArn" "before" SSM automation execution
      | TaskDefinitionArn                               | ClusterName                               | ServiceName                              |
      | {{cfn-output:ECSEC2Template>ECSTaskDefinition}} | {{cfn-output:ECSEC2Template>ClusterName}} | {{cfn-output:ECSEC2Template>ECSService}} |
    When SSM automation document "Digito-ScaleECSServiceSOP_2020-04-01" executed
      | ClusterName                               | ServiceName                              | NewTaskDefinitionArn                   | AutomationAssumeRole                                                           |
      | {{cfn-output:ECSEC2Template>ClusterName}} | {{cfn-output:ECSEC2Template>ECSService}} | {{cache:before>NewTaskDefinitionArn}}  | {{cfn-output:AutomationAssumeRoleTemplate>DigitoScaleECSServiceSOPAssumeRole}} |
    Then SSM automation document "Digito-ScaleECSServiceSOP_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache number of tasks as "AmountOFTasks" "after" SSM execution
      | ECSService                                | ECSCluster                                |
      | {{cfn-output:ECSEC2Template>ECSService}}  | {{cfn-output:ECSEC2Template>ClusterName}} |
    And assert "AmountOFTasks" at "before" became equal to "AmountOFTasks" at "after"


  Scenario: Execute SSM automation document Digito-ScaleECSServiceSOP_2020-04-01 on EC2. No NewTaskDefinition. No NumberOfTasks.
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                       | ResourceType | VPC                      |  PublicSubnetOne                    | PublicSubnetTwo                    |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                             | SHARED       |                          |                                     |                                    |
      | resource_manager/cloud_formation_templates/ECSEC2Template.yml                         | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>PublicSubnetOne}}  | {{cfn-output:VPC>PublicSubnetTwo}} |
      | documents/ecs/sop/scale_service/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                          |                                     |                                    |
    And published "Digito-ScaleECSServiceSOP_2020-04-01" SSM document
    And waits until the ECSService is stable (tasks started or stopped)
      | ECSService                                | ECSCluster                                |
      | {{cfn-output:ECSEC2Template>ECSService}}  | {{cfn-output:ECSEC2Template>ClusterName}} |
    And cache number of tasks as "AmountOFTasks" "before" SSM execution
      | ECSService                                | ECSCluster                                |
      | {{cfn-output:ECSEC2Template>ECSService}}  | {{cfn-output:ECSEC2Template>ClusterName}} |
    When SSM automation document "Digito-ScaleECSServiceSOP_2020-04-01" executed
      | ClusterName                               | ServiceName                               | AutomationAssumeRole                                                           |
      | {{cfn-output:ECSEC2Template>ClusterName}} | {{cfn-output:ECSEC2Template>ECSService}}  | {{cfn-output:AutomationAssumeRoleTemplate>DigitoScaleECSServiceSOPAssumeRole}} |
    Then SSM automation document "Digito-ScaleECSServiceSOP_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache number of tasks as "AmountOFTasks" "after" SSM execution
      | ECSService                                | ECSCluster                                |
      | {{cfn-output:ECSEC2Template>ECSService}}  | {{cfn-output:ECSEC2Template>ClusterName}} |
    And assert "AmountOFTasks" at "before" became equal to "AmountOFTasks" at "after"


  Scenario: Execute SSM automation document Digito-ScaleECSServiceSOP_2020-04-01 on EC2. No NewTaskDefinition. NumberOfTasks.
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                       | ResourceType | VPC                      |  PublicSubnetOne                    | PublicSubnetTwo                    |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                             | SHARED       |                          |                                     |                                    |
      | resource_manager/cloud_formation_templates/ECSEC2Template.yml                         | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>PublicSubnetOne}}  | {{cfn-output:VPC>PublicSubnetTwo}} |
      | documents/ecs/sop/scale_service/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                          |                                     |                                    |
    And published "Digito-ScaleECSServiceSOP_2020-04-01" SSM document
    And create new task definition and cache it as "NewTaskDefinitionArn" "before" SSM automation execution
      | TaskDefinitionArn                               | ClusterName                               | ServiceName                              |
      | {{cfn-output:ECSEC2Template>ECSTaskDefinition}} | {{cfn-output:ECSEC2Template>ClusterName}} | {{cfn-output:ECSEC2Template>ECSService}} |
    When SSM automation document "Digito-ScaleECSServiceSOP_2020-04-01" executed
      | ClusterName                               | ServiceName                              | NumberOfTasks | AutomationAssumeRole                                                          |
      | {{cfn-output:ECSEC2Template>ClusterName}} | {{cfn-output:ECSEC2Template>ECSService}} | 2             | {{cfn-output:AutomationAssumeRoleTemplate>DigitoScaleECSServiceSOPAssumeRole}} |
    Then SSM automation document "Digito-ScaleECSServiceSOP_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache number of tasks as "AmountOFTasks" "after" SSM execution
      | ECSService                                | ECSCluster                                |
      | {{cfn-output:ECSEC2Template>ECSService}}  | {{cfn-output:ECSEC2Template>ClusterName}} |
    And assert "AmountOFTasks" at "after" became equal to "2"


  Scenario: Execute SSM automation document Digito-ScaleECSServiceSOP_2020-04-01 on EC2. No NewTaskDefinition. Memory and CPU.
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                       | ResourceType | VPC                      |  PublicSubnetOne                    | PublicSubnetTwo                    |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                             | SHARED       |                          |                                     |                                    |
      | resource_manager/cloud_formation_templates/ECSEC2Template.yml                         | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>PublicSubnetOne}}  | {{cfn-output:VPC>PublicSubnetTwo}} |
      | documents/ecs/sop/scale_service/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                          |                                     |                                    |
    And published "Digito-ScaleECSServiceSOP_2020-04-01" SSM document
    When SSM automation document "Digito-ScaleECSServiceSOP_2020-04-01" executed
      | ClusterName                               | ServiceName                              | TaskDefinitionCPU | TaskDefinitionRAM | AutomationAssumeRole                                                           |
      | {{cfn-output:ECSEC2Template>ClusterName}} | {{cfn-output:ECSEC2Template>ECSService}} | 256               | 512               | {{cfn-output:AutomationAssumeRoleTemplate>DigitoScaleECSServiceSOPAssumeRole}} |
    Then SSM automation document "Digito-ScaleECSServiceSOP_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache memory and cpu as "ContainerDefinitions" "after" SSM execution
      | TaskDefinitionArn                               |
      | {{cfn-output:ECSEC2Template>ECSTaskDefinition}} |
    And assert "ContainerDefinitions" at "after" became equal to CPU and Memory
      | TaskDefinitionCPU | TaskDefinitionRAM |
      | 256               | 512               |
