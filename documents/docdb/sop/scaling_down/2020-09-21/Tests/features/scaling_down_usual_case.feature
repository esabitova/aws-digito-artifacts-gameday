# @docdb
Feature: SSM automation document Digito-ScaleDownDocumentDBClusterSOP_2020-09-21

  Scenario: Execute SSM automation document Digito-ScaleDownDocumentDBClusterSOP_2020-09-21
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath     | ResourceType |
      | resource_manager/cloud_formation_templates/DocDbTemplate.yml  | ON_DEMAND    |
      | documents/docdb/sop/scaling_down/2020-09-21/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-ScaleDownDocumentDBClusterSOP_2020-09-21" SSM document
    # Add any pre-execution caching and setup steps here

    When SSM automation document "Digito-ScaleDownDocumentDBClusterSOP_2020-09-21" executed
    # Add other parameter names below
      | DBClusterIdentifier             | AutomationAssumeRole                                    |
    # Replace parameter values to point to the corresponding outputs in cloudformation template
      | {{cfn-output:DocDbTemplate>DBClusterIdentifier}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoScaleDownDocumentDBClusterSOPAssumeRole}} |
    # Add other steps that should run parallel to the document here

    Then SSM automation document "Digito-ScaleDownDocumentDBClusterSOP_2020-09-21" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    # Add any post-execution caching and validation here