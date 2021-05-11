@${serviceName}
Feature: SSM automation document ${name}

  Scenario: Execute SSM automation document ${name} in rollback
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath     | ResourceType |
      | resource_manager/cloud_formation_templates/${cfnTemplateName}.yml  | ON_DEMAND    |
      | documents/${serviceName}/${documentType}/${name}/${date}/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "${documentName}" SSM document
    # Add any pre-execution caching and setup steps here

    When SSM automation document "${documentName}" executed
    # Add other parameter names below
      | ${primaryResourceIdentifier}                                   | AutomationAssumeRole                                                           | ${alarmPrefix}AlarmName                                 |
    # Replace parameter values to point to the corresponding outputs in cloudformation template
      | {{cfn-output:${cfnTemplateName}>${resourceIdOutput}}} | {{cfn-output:AutomationAssumeRoleTemplate>${roleName}}} | {{cfn-output:${cfnTemplateName}>${alarmNameOutput}}} |
    # Add other steps that should parallel to the document here
    And Wait for the SSM automation document "${documentName}" execution is on step "AssertAlarmToBeRed" in status "InProgress" for "600" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And terminate "${documentName}" SSM automation document
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    Then Wait for the SSM automation document "${documentName}" execution is on step "TriggerRollback" in status "Success" for "240" seconds
      | ExecutionId               |
      | {{cache:SsmExecutionId>1}}|
    And SSM automation document "${documentName}" execution in status "Cancelled"
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|
    And cache rollback execution id
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|
    And SSM automation document "${documentName}" execution in status "Success"
      |ExecutionId               |
      |{{cache:SsmExecutionId>2}}|
    # Add any post-execution caching and validation here
