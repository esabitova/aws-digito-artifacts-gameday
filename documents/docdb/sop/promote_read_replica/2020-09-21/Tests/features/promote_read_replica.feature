@docdb
Feature: SSM automation document to promote read replica.

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document for promoting DocDb replica to the primary instance
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                | ResourceType | KmsKey                              |
      | resource_manager/cloud_formation_templates/shared/KMS.yml                                      | SHARED       |                                     |
      | resource_manager/cloud_formation_templates/DocDbTemplate.yml                                   | ON_DEMAND    | {{cfn-output:KMS>EncryptAtRestKey}} |
      | documents/docdb/sop/promote_read_replica/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                                     |
    And published "Digito-PromoteReadReplica_2020-09-21" SSM document
    And cache replica instance identifier as "DBInstanceReplicaIdentifier" at step "before"
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    When SSM automation document "Digito-PromoteReadReplica_2020-09-21" executed
      | DBClusterIdentifier                              | DBInstanceReplicaIdentifier                  | AutomationAssumeRole                                                           |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} | {{cache:before>DBInstanceReplicaIdentifier}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoPromoteReadReplicaAssumeRole}} |

    Then SSM automation document "Digito-PromoteReadReplica_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And sleep for "120" seconds
    And assert if the cluster member is the primary instance
      | DBClusterIdentifier                              | DBInstanceIdentifier                         |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} | {{cache:before>DBInstanceReplicaIdentifier}} |