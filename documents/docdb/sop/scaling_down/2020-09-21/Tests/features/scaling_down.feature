@docdb
Feature: SSM automation document for scaling down DocDb instances.

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document for scaling down DocumentDb instances
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                        | ResourceType |
      | resource_manager/cloud_formation_templates/DocDbTemplate.yml                           | ON_DEMAND    |
      | documents/docdb/sop/scaling_down/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
      | documents/docdb/sop/scaling_up/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml   | ASSUME_ROLE  |
    And published "Digito-ScalingDown_2020-09-21" SSM document
    And published "Digito-ScalingUp_2020-09-21" SSM document
    And cache current number of clusters as "NumberOfInstances" "before" SSM automation execution
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    And SSM automation document "Digito-ScalingDown_2020-09-21" executed
      | DBClusterIdentifier                              | DBInstanceReplicaIdentifier                              | AutomationAssumeRole                                                    |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} | {{cfn-output:DocDbTemplate>DBInstanceReplicaIdentifier}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoScalingDownAssumeRole}} |

    When SSM automation document "Digito-ScalingDown_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache current number of clusters as "NumberOfInstances" "after" SSM automation execution
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |

    Then assert "NumberOfInstances" at "before" became not equal to "NumberOfInstances" at "after"
    And SSM automation document "Digito-ScalingUp_2020-09-21" executed
      | DBClusterIdentifier                              | DBInstanceReplicaIdentifier                              | AutomationAssumeRole                                                  |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} | {{cfn-output:DocDbTemplate>DBInstanceReplicaIdentifier}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoScalingUpAssumeRole}} |

    When SSM automation document "Digito-ScalingUp_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>2}} |
    And cache current number of clusters as "NumberOfInstances" "finally" SSM automation execution
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    Then assert "NumberOfInstances" at "before" became equal to "NumberOfInstances" at "finally"

