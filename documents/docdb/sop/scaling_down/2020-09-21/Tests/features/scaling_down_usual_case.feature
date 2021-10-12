@docdb
Feature: SSM automation document to scale down the Amazon DocumentDb cluster

  Scenario: Execute SSM automation document Digito-ScaleDownDocumentDBClusterSOP_2020-09-21 to scale down Amazon DocumentDB cluster. NumberOfDBInstancesToDelete.
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                        | ResourceType | VPC                      | VPCCIDR                    | PrivateSubnet01                                | PrivateSubnet02                                | KmsKey                              |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                              | SHARED       |                          |                            |                                                |                                                |                                     |
      | resource_manager/cloud_formation_templates/shared/KMS.yml                              | SHARED       |                          |                            |                                                |                                                |                                     |
      | resource_manager/cloud_formation_templates/DocDbTemplateWithThreeReplicas.yml          | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>VPCCidr}} | {{cfn-output:VPC>PrivateSubnetWithInternet01}} | {{cfn-output:VPC>PrivateSubnetWithInternet02}} | {{cfn-output:KMS>EncryptAtRestKey}} |
      | documents/docdb/sop/scaling_down/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                          |                            |                                                |                                                |                                     |
    And published "Digito-ScaleDownDocumentDBClusterSOP_2020-09-21" SSM document
    And wait for instances to be available for "120" seconds
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplateWithThreeReplicas>DBClusterIdentifier}} |
    And cache cluster instances metadata as "DBInstances" at step "before"
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplateWithThreeReplicas>DBClusterIdentifier}} |
    And cache current number of available instances as "NumberOfInstances" "before" SSM automation execution
      | DBClusterIdentifier                                           |
      | {{cfn-output:DocDbTemplateWithThreeReplicas>DBClusterIdentifier}} |
    And cache values to "before"
      | DBClusterIdentifier                                           |
      | {{cfn-output:DocDbTemplateWithThreeReplicas>DBClusterIdentifier}} |

    When SSM automation document "Digito-ScaleDownDocumentDBClusterSOP_2020-09-21" executed
      | DBClusterIdentifier                                               | NumberOfDBInstancesToDelete | AutomationAssumeRole                                                                      |
      | {{cfn-output:DocDbTemplateWithThreeReplicas>DBClusterIdentifier}} | 2                           | {{cfn-output:AutomationAssumeRoleTemplate>DigitoScaleDownDocumentDBClusterSOPAssumeRole}} |
    Then SSM automation document "Digito-ScaleDownDocumentDBClusterSOP_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache current number of available instances as "ActualNumberOfInstances" "after" SSM automation execution
      | DBClusterIdentifier                                           |
      | {{cfn-output:DocDbTemplateWithThreeReplicas>DBClusterIdentifier}} |
    Then assert the difference between "NumberOfInstances" at "before" and "ActualNumberOfInstances" at "after" became "2"

  Scenario: Execute SSM automation document Digito-ScaleDownDocumentDBClusterSOP_2020-09-21 to scale down Amazon DocumentDB cluster. DBInstancesIdentifiersToDelete.
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                        | ResourceType | VPC                      | VPCCIDR                    | PrivateSubnet01                                | PrivateSubnet02                                | KmsKey                              |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                              | SHARED       |                          |                            |                                                |                                                |                                     |
      | resource_manager/cloud_formation_templates/shared/KMS.yml                              | SHARED       |                          |                            |                                                |                                                |                                     |
      | resource_manager/cloud_formation_templates/DocDbTemplateWithThreeReplicas.yml          | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>VPCCidr}} | {{cfn-output:VPC>PrivateSubnetWithInternet01}} | {{cfn-output:VPC>PrivateSubnetWithInternet02}} | {{cfn-output:KMS>EncryptAtRestKey}} |
      | documents/docdb/sop/scaling_down/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                          |                            |                                                |                                                |                                     |
    And published "Digito-ScaleDownDocumentDBClusterSOP_2020-09-21" SSM document
    And wait for instances to be available for "120" seconds
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplateWithThreeReplicas>DBClusterIdentifier}} |
    And cache replica instance identifier as "DBInstanceReplicaIdentifier" at step "before"
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplateWithThreeReplicas>DBClusterIdentifier}} |
    And cache cluster instances metadata as "DBInstances" at step "before"
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplateWithThreeReplicas>DBClusterIdentifier}} |
    And cache current number of available instances as "NumberOfInstances" "before" SSM automation execution
      | DBClusterIdentifier                                           |
      | {{cfn-output:DocDbTemplateWithThreeReplicas>DBClusterIdentifier}} |
    And cache values to "before"
      | DBClusterIdentifier                                           |
      | {{cfn-output:DocDbTemplateWithThreeReplicas>DBClusterIdentifier}} |

    When SSM automation document "Digito-ScaleDownDocumentDBClusterSOP_2020-09-21" executed
      | DBClusterIdentifier                                               | DBInstancesIdentifiersToDelete               | AutomationAssumeRole                                                                      |
      | {{cfn-output:DocDbTemplateWithThreeReplicas>DBClusterIdentifier}} | {{cache:before>DBInstanceReplicaIdentifier}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoScaleDownDocumentDBClusterSOPAssumeRole}} |
    Then SSM automation document "Digito-ScaleDownDocumentDBClusterSOP_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache current number of available instances as "ActualNumberOfInstances" "after" SSM automation execution
      | DBClusterIdentifier                                           |
      | {{cfn-output:DocDbTemplateWithThreeReplicas>DBClusterIdentifier}} |
    Then assert the difference between "NumberOfInstances" at "before" and "ActualNumberOfInstances" at "after" became "1"