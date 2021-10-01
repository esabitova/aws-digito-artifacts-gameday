@docdb
Feature: SSM automation document to create more instances in Amazon DocumentDb cluster

  Scenario: Execute SSM automation document Digito-ScaleUpDocumentDBClusterSOP_2020-09-21 to scale up Amazon DocumentDB cluster
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                      | ResourceType | VPC                      | VPCCIDR                    | PrivateSubnet01                                | PrivateSubnet02                                | KmsKey                              |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                            | SHARED       |                          |                            |                                                |                                                |                                     |
      | resource_manager/cloud_formation_templates/shared/KMS.yml                            | SHARED       |                          |                            |                                                |                                                |                                     |
      | resource_manager/cloud_formation_templates/DocDbTemplateWithoutCanary.yml            | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>VPCCidr}} | {{cfn-output:VPC>PrivateSubnetWithInternet01}} | {{cfn-output:VPC>PrivateSubnetWithInternet02}} | {{cfn-output:KMS>EncryptAtRestKey}} |
      | documents/docdb/sop/scaling_up/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                          |                            |                                                |                                                |                                     |
    And published "Digito-ScaleUpDocumentDBClusterSOP_2020-09-21" SSM document
    And cache current number of available instances as "NumberOfInstances" "before" SSM automation execution
      | DBClusterIdentifier                                           |
      | {{cfn-output:DocDbTemplateWithoutCanary>DBClusterIdentifier}} |
    And cache values to "before"
      | DBClusterIdentifier                                           |
      | {{cfn-output:DocDbTemplateWithoutCanary>DBClusterIdentifier}} |

    When SSM automation document "Digito-ScaleUpDocumentDBClusterSOP_2020-09-21" executed
      | DBClusterIdentifier                                           | DBInstanceClass | NumberOfInstancesToCreate | AutomationAssumeRole                                                                    |
      | {{cfn-output:DocDbTemplateWithoutCanary>DBClusterIdentifier}} | current         | 3                         | {{cfn-output:AutomationAssumeRoleTemplate>DigitoScaleUpDocumentDBClusterSOPAssumeRole}} |
    Then SSM automation document "Digito-ScaleUpDocumentDBClusterSOP_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache current number of available instances as "ActualNumberOfInstances" "after" SSM automation execution
      | DBClusterIdentifier                                           |
      | {{cfn-output:DocDbTemplateWithoutCanary>DBClusterIdentifier}} |
    Then assert the difference between "ActualNumberOfInstances" at "after" and "NumberOfInstances" at "before" became "3"