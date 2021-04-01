@rds @promote_non_aurora_replica @integration
Feature: SSM automation document for promoting non aurora replica sop.
  Exercise SSM automation document for promoting non aurora replica.

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document to promote non aurora replica
    Given the cloud formation templates as integration test resources
      |CfnTemplatePath                                                                                   |ResourceType|DBInstanceClass|AllocatedStorage|
      |resource_manager/cloud_formation_templates/RdsCfnTemplate.yml                                     |   ON_DEMAND|    db.t3.small|              20|
      |documents/rds/sop/promote_non_aurora_replica/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml| ASSUME_ROLE|               |                |
    And published "Digito-RdsPromoteReadReplica_2020-04-01" SSM document

    When SSM automation document "Digito-RdsPromoteReadReplica_2020-04-01" executed
      |DbInstanceIdentifier                    |AutomationAssumeRole                                                             |Dryrun|
      |{{cfn-output:RdsCfnTemplate>InstanceId}}|{{cfn-output:AutomationAssumeRoleTemplate>DigitoRdsPromoteReadReplicaAssumeRole}}|  true|
    Then SSM automation document "Digito-RdsPromoteReadReplica_2020-04-01" execution in status "Success"
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|
