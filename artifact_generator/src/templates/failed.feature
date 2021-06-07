@${serviceName}
Feature: SSM automation document ${documentName}

  Scenario: Execute SSM automation document ${documentName} to test failure case
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath     | ResourceType |
      | resource_manager/cloud_formation_templates/${cfnTemplateName}.yml  | ON_DEMAND    |
      | documents/${serviceName}/${documentType}/${name}/${date}/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "${documentName}" SSM document
    # Add any pre-execution caching and setup steps here

    When SSM automation document "${documentName}" executed
    # Add other parameter names below
      | ${primaryResourceIdentifier}                                       | AutomationAssumeRole                                                              | ${alarmPrefix}AlarmName                                                |
    # Replace parameter values to point to the corresponding outputs in cloudformation template
      | {{cfn-output:${cfnTemplateName}>${resourceIdOutput}}} | {{cfn-output:AutomationAssumeRoleTemplate>${roleName}}} | {{cfn-output:${cfnTemplateName}>AlwaysOKAlarm}} |
    # Add other steps that should parallel to the document here
    And Wait for the SSM automation document "${documentName}" execution is on step "AssertAlarmToBeRed" in status "TimedOut" for "1000" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    # Add any step required to rectify the alarm here

    Then Wait for the SSM automation document "${documentName}" execution is on step "AssertAlarmToBeGreen" in status "Success" for "1000" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And SSM automation document "${documentName}" execution in status "TimedOut"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    # Add any post-execution caching and validation here
