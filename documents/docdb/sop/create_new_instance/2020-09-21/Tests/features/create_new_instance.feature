@docdb
Feature: SSM automation document to recover the database into a known good state.

  Scenario: Create a new instance in a specified AZ/Region
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                               | ResourceType | VPC                      | VPCCIDR                    | PrivateSubnet01                                | PrivateSubnet02                                | KmsKey                              |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                                     | SHARED       |                          |                            |                                                |                                                |                                     |
      | resource_manager/cloud_formation_templates/shared/KMS.yml                                     | SHARED       |                          |                            |                                                |                                                |                                     |
      | resource_manager/cloud_formation_templates/DocDbTemplate.yml                                  | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>VPCCidr}} | {{cfn-output:VPC>PrivateSubnetWithInternet01}} | {{cfn-output:VPC>PrivateSubnetWithInternet02}} | {{cfn-output:KMS>EncryptAtRestKey}} |
      | documents/docdb/sop/create_new_instance/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                          |                            |                                                |                                                |                                     |
    And published "Digito-CreateNewDocDbInstance_2020-09-21" SSM document
    And cache generated instance identifier as "InstanceId" at step "before"
    And cache one of cluster azs in property "RandomClusterAZ" in step "before"
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    And cache current number of instances as "NumberOfInstances" "before" SSM automation execution
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    And cache property "ExpectedAvailabilityZone" in step "before" SSM automation execution
      | Value                            |
      | {{cache:before>RandomClusterAZ}} |
    When SSM automation document "Digito-CreateNewDocDbInstance_2020-09-21" executed
      | DBClusterIdentifier                              | DBInstanceIdentifier            | AvailabilityZone                 | AutomationAssumeRole                                                          |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} | {{{{cache:before>InstanceId}}}} | {{cache:before>RandomClusterAZ}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoCreateNewInstanceAssumeRole}} |
    Then SSM automation document "Digito-CreateNewDocDbInstance_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache current number of instances as "ActualNumberOfInstances" "after" SSM automation execution
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    Then sleep for "60" seconds
    And cache az in property "ActualAvailabilityZone" in step "after" SSM automation execution
      | DBInstanceIdentifier            |
      | {{{{cache:before>InstanceId}}}} |
    Then assert "NumberOfInstances" at "before" less than "ActualNumberOfInstances" at "after"
    Then assert "ExpectedAvailabilityZone" at "before" became equal to "ActualAvailabilityZone" at "after"


  Scenario: Create a new instance without specifying AZ
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                               | ResourceType | VPC                      | VPCCIDR                    | PrivateSubnet01                                | PrivateSubnet02                                | KmsKey                              |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                                     | SHARED       |                          |                            |                                                |                                                |                                     |
      | resource_manager/cloud_formation_templates/shared/KMS.yml                                     | SHARED       |                          |                            |                                                |                                                |                                     |
      | resource_manager/cloud_formation_templates/DocDbTemplate.yml                                  | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>VPCCidr}} | {{cfn-output:VPC>PrivateSubnetWithInternet01}} | {{cfn-output:VPC>PrivateSubnetWithInternet02}} | {{cfn-output:KMS>EncryptAtRestKey}} |
      | documents/docdb/sop/create_new_instance/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                          |                            |                                                |                                                |                                     |
    And published "Digito-CreateNewDocDbInstance_2020-09-21" SSM document
    And cache generated instance identifier as "InstanceId" at step "before"
    And cache current number of instances as "NumberOfInstances" "before" SSM automation execution
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    When SSM automation document "Digito-CreateNewDocDbInstance_2020-09-21" executed
      | DBClusterIdentifier                              | DBInstanceIdentifier            | AutomationAssumeRole                                                          |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} | {{{{cache:before>InstanceId}}}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoCreateNewInstanceAssumeRole}} |
    Then SSM automation document "Digito-CreateNewDocDbInstance_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache current number of instances as "ActualNumberOfInstances" "after" SSM automation execution
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
    Then sleep for "60" seconds
    And cache az in property "ActualAvailabilityZone" in step "after" SSM automation execution
      | DBInstanceIdentifier            |
      | {{{{cache:before>InstanceId}}}} |
    Then assert "NumberOfInstances" at "before" less than "ActualNumberOfInstances" at "after"
    Then assert instance AZ value "ActualAvailabilityZone" at "after" is one of cluster AZs
      | DBClusterIdentifier                              |
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} |
