@docdb
Feature: SSM automation document for scaling down DocDb instances.

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document for scaling down DocumentDb instances
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                        | ResourceType |
      | resource_manager/cloud_formation_templates/DocDbTemplate.yml                           | ON_DEMAND    |
      | documents/docdb/sop/scaling_down/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-ScalingDown_2020-09-21" SSM document
    When SSM automation document "Digito-ScalingDown_2020-09-21" executed
      | DBClusterIdentifier                                   |  DBInstanceReplicaIdentifier                              | AutomationAssumeRole                                                    |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}}      |  {{cfn-output:DocDbTemplate>DBInstanceReplicaIdentifier}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoScalingDownAssumeRole}} |

    Then SSM automation document "Digito-ScalingDown_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |