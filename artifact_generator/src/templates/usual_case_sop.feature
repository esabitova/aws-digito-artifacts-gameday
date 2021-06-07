@${serviceName}
Feature: SSM automation document ${documentName}

  Scenario: Execute SSM automation document ${documentName}
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath     | ResourceType |
      | resource_manager/cloud_formation_templates/${cfnTemplateName}.yml  | ON_DEMAND    |
      | documents/${serviceName}/${documentType}/${name}/${date}/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "${documentName}" SSM document
    # Add any pre-execution caching and setup steps here

    When SSM automation document "${documentName}" executed
    # Add other parameter names below
      | ${primaryResourceIdentifier}             | AutomationAssumeRole                                    |
    # Replace parameter values to point to the corresponding outputs in cloudformation template
      | {{cfn-output:${cfnTemplateName}>${resourceIdOutput}}} | {{cfn-output:AutomationAssumeRoleTemplate>${roleName}}} |
    # Add other steps that should run parallel to the document here

    Then SSM automation document "${documentName}" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    # Add any post-execution caching and validation here