@docdb
Feature: SSM automation document for scaling up DocDb instances.

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document for scaling up DocumentDb instances
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                      | ResourceType | VPC                      | VPCCIDR                    | PrivateSubnet01                                | PrivateSubnet02                                |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                            | SHARED       |                          |                            |                                                |                                                |
      | resource_manager/cloud_formation_templates/DocDbTemplate.yml                         | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>VPCCidr}} | {{cfn-output:VPC>PrivateSubnetWithInternet01}} | {{cfn-output:VPC>PrivateSubnetWithInternet02}} |
      | documents/docdb/sop/scaling_up/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                          |                            |                                                |                                                |
    And published "Digito-ScalingUp_2020-09-21" SSM document
    And cache generated instance identifier as "InstanceId" at step "before"
    And cache current number of instances as "NumberOfInstances" "before" SSM automation execution
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    And SSM automation document "Digito-ScalingUp_2020-09-21" executed
      | DBClusterIdentifier                              | DBInstanceReplicaIdentifier | AutomationAssumeRole                                                  |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} | {{cache:before>InstanceId}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoScalingUpAssumeRole}} |

    When SSM automation document "Digito-ScalingUp_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache current number of instances as "NumberOfInstances" "after" SSM automation execution
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |

    Then assert "NumberOfInstances" at "before" became not equal to "NumberOfInstances" at "after"
