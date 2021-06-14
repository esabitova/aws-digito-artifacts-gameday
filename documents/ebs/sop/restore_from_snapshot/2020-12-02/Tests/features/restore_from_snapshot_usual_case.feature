# @ebs
Feature: SSM automation document Digito-EBSRestoreFromSnapshot_2020-12-02

  Scenario: Execute SSM automation document Digito-EBSRestoreFromSnapshot_2020-12-02
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath     | ResourceType |
      | resource_manager/cloud_formation_templates/EbsTemplate.yml  | ON_DEMAND    |
      | documents/ebs/sop/restore_from_snapshot/2020-12-02/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-EBSRestoreFromSnapshot_2020-12-02" SSM document
    # Add any pre-execution caching and setup steps here

    When SSM automation document "Digito-EBSRestoreFromSnapshot_2020-12-02" executed
    # Add other parameter names below
      | VolumeId             | AutomationAssumeRole                                    |
    # Replace parameter values to point to the corresponding outputs in cloudformation template
      | {{cfn-output:EbsTemplate>VolumeId}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoEbsRestoreFromSnapshotAssumeRole}} |
    # Add other steps that should run parallel to the document here

    Then SSM automation document "Digito-EBSRestoreFromSnapshot_2020-12-02" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    # Add any post-execution caching and validation here