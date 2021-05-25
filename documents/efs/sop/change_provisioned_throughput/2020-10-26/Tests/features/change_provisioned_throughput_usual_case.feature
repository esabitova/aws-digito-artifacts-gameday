@efs
Feature: SSM automation document Digito-EFSChangeProvisionedThroughput_2020-10-26

  Scenario: Execute SSM automation document Digito-EFSChangeProvisionedThroughput_2020-10-26
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                       | ResourceType |
      | resource_manager/cloud_formation_templates/EFSTemplate.yml                                            | DEDICATED    |
      | documents/efs/sop/change_provisioned_throughput/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-EFSChangeProvisionedThroughput_2020-10-26" SSM document
    And cache filesystem property "$.ProvisionedThroughputInMibps" as "OldProvisionedThroughput" "before" SSM automation execution
      | FileSystemID                     |
      | {{cfn-output:EFSTemplate>EFSID}} |
    And generate different value of "ProvisionedThroughput" than "OldProvisionedThroughput" from "1" to "1024" as "ExpectedProvisionedThroughput" "before" SSM automation execution
      | OldProvisionedThroughput                  |
      | {{cache:before>OldProvisionedThroughput}} |
    When SSM automation document "Digito-EFSChangeProvisionedThroughput_2020-10-26" executed
      | FileSystemID                     | ProvisionedThroughput                          | AutomationAssumeRole                                                                        |
      | {{cfn-output:EFSTemplate>EFSID}} | {{cache:before>ExpectedProvisionedThroughput}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoEfsChangeProvisionedThroughputAssumeRole}}  |

    Then SSM automation document "Digito-EFSChangeProvisionedThroughput_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache filesystem property "$.ProvisionedThroughputInMibps" as "ActualProvisionedThroughput" "after" SSM automation execution
      | FileSystemID                     |
      | {{cfn-output:EFSTemplate>EFSID}} |

    Then assert "ExpectedProvisionedThroughput" at "before" became equal to "ActualProvisionedThroughput" at "after"

    And assert "OldProvisionedThroughput" at "before" became not equal to "ActualProvisionedThroughput" at "after"
