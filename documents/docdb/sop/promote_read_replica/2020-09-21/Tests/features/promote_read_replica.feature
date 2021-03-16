@docdb
Feature: SSM automation document to promote read replica.

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document for promoting DocDb replica to the primary instance
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                | ResourceType |
      | resource_manager/cloud_formation_templates/DocDbTemplate.yml                                   | ON_DEMAND    |
      | documents/docdb/sop/promote_read_replica/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-PromoteReadReplica_2020-09-21" SSM document
    When SSM automation document "Digito-PromoteReadReplica_2020-09-21" executed
      | DBClusterIdentifier                                   | DBInstanceReplicaIdentifier                             |AutomationAssumeRole                                                           |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}}      |{{cfn-output:DocDbTemplate>DBInstanceReplicaIdentifier}} |{{cfn-output:AutomationAssumeRoleTemplate>DigitoPromoteReadReplicaAssumeRole}} |

    Then SSM automation document "Digito-PromoteReadReplica_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
