@ecs
Feature: SSM automation document Digito-DrainECSContainerInstancesTest_2020-04-01

  Scenario: Execute SSM automation document Digito-DrainECSContainerInstancesTest_2020-04-01
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                    | ResourceType |
      | resource_manager/cloud_formation_templates/ECSEC2Template.yml                                      | ON_DEMAND    |
      | documents/ecs/test/drain_container_instances/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-DrainECSContainerInstancesTest_2020-04-01" SSM document
    # Add any pre-execution caching and setup steps here

    When SSM automation document "Digito-DrainECSContainerInstancesTest_2020-04-01" executed
      # Add other parameter names below
      | ClusterName                               | AutomationAssumeRole                                                                       | SyntheticAlarmName                           |
      # Replace parameter values to point to the corresponding outputs in cloudformation template
      | {{cfn-output:ECSEC2Template>ClusterName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoDrainECSContainerInstancesTestAssumeRole}} | {{cfn-output:ECSFISTemplate>SyntheticAlarm}} |
    # Add other steps that should run parallel to the document here

    Then SSM automation document "Digito-DrainECSContainerInstancesTest_2020-04-01" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
# Add any post-execution caching and validation here