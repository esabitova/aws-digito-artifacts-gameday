@ecs
Feature: SSM automation document Digito-ScaleService_2020-04-01

  Scenario: Execute SSM automation document Digito-ScaleService_2020-04-01 on Fargate to apply new task definition to service
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                       | ResourceType | VPC                      | PublicSubnetOne                    |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                             | SHARED       |                          |                                    |
      | resource_manager/cloud_formation_templates/ECSFargateTemplate.yml                     | ON_DEMAND    | {{cfn-output:VPC>VPCId}} |{{cfn-output:VPC>PublicSubnetOne}}  |
      | documents/ecs/sop/scale_service/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                          |                                    |
    And published "Digito-ScaleService_2020-04-01" SSM document
    And create new task definition and cache it as "NewTaskDefinitionArn" "before" SSM automation execution
      | TaskDefinitionArn                                   | ClusterName                                   | ServiceName                                  |
      | {{cfn-output:ECSFargateTemplate>ECSTaskDefinition}} | {{cfn-output:ECSFargateTemplate>ClusterName}} | {{cfn-output:ECSFargateTemplate>ECSService}} |
    When SSM automation document "Digito-ScaleService_2020-04-01" executed
      | ClusterName                                   | ServiceName                                  | NewTaskDefinitionArn                   | NumberOfTasks  | AutomationAssumeRole                                                        |
      | {{cfn-output:ECSFargateTemplate>ClusterName}} | {{cfn-output:ECSFargateTemplate>ECSService}} | {{cache:before>NewTaskDefinitionArn}}  |  1             | {{cfn-output:AutomationAssumeRoleTemplate>DigitoEcsScaleServiceAssumeRole}} |

    Then SSM automation document "Digito-ScaleService_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |