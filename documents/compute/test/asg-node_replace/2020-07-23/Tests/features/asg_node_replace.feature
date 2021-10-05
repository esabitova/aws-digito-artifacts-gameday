@asg @integration @node_replace
Feature: SSM automation document ASG node replace testing
  Exercise ASG node replace injection

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation node replace on ASG instances
    Given the cached input parameters
      |InstanceType|TestDurationInMinutes|
      |    t2.small|                    5|
    And the cloud formation templates as integration test resources
      |CfnTemplatePath                                                                              |ResourceType|InstanceType          |
      |resource_manager/cloud_formation_templates/AsgCfnTemplate.yml                                |   ON_DEMAND|{{cache:InstanceType}}|
      |documents/compute/test/asg-node_replace/2020-07-23/Documents/AutomationAssumeRoleTemplate.yml| ASSUME_ROLE|                      |
    And published "Digito-RefreshAsgInstances_2020-07-23" SSM document

    When SSM automation document "Digito-RefreshAsgInstances_2020-07-23" executed
      |AutoScalingGroupName                               |AutomationAssumeRole                                                           |SyntheticAlarmName                          |
      |{{cfn-output:AsgCfnTemplate>AutoScalingGroupName}} |{{cfn-output:AutomationAssumeRoleTemplate>DigitoRefreshAsgInstancesAssumeRole}}|{{cfn-output:AsgCfnTemplate>SyntheticAlarm}}|
    Then SSM automation document "Digito-RefreshAsgInstances_2020-07-23" execution in status "Success"
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|


  Scenario: Create AWS resources using CloudFormation template and execute SSM automation node replace on ASG instances in rollback mode
    Given the cached input parameters
      |InstanceType|TestDurationInMinutes|
      |    t2.small|                    5|
    And the cloud formation templates as integration test resources
      |CfnTemplatePath                                                                              |ResourceType|InstanceType          |
      |resource_manager/cloud_formation_templates/AsgCfnTemplate.yml                                |   ON_DEMAND|{{cache:InstanceType}}|
      |documents/compute/test/asg-node_replace/2020-07-23/Documents/AutomationAssumeRoleTemplate.yml| ASSUME_ROLE|                      |
    And published "Digito-RefreshAsgInstances_2020-07-23" SSM document

    When SSM automation document "Digito-RefreshAsgInstances_2020-07-23" executed
      |AutoScalingGroupName                               |AutomationAssumeRole                                                           |SyntheticAlarmName                          |
      |{{cfn-output:AsgCfnTemplate>AutoScalingGroupName}} |{{cfn-output:AutomationAssumeRoleTemplate>DigitoRefreshAsgInstancesAssumeRole}}|{{cfn-output:AsgCfnTemplate>SyntheticAlarm}}|

    And Wait for the SSM automation document "Digito-RefreshAsgInstances_2020-07-23" execution is on step "StartInstanceRefresh" in status "Success" for "180" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    Then terminate "Digito-RefreshAsgInstances_2020-07-23" SSM automation document
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|

    Then Wait for the SSM automation document "Digito-RefreshAsgInstances_2020-07-23" execution is on step "TriggerRollback" in status "Success" for "240" seconds
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|

    Then SSM automation document "Digito-RefreshAsgInstances_2020-07-23" execution in status "Cancelled"
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|

    Then cache rollback execution id
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|

    Then SSM automation document "Digito-RefreshAsgInstances_2020-07-23" execution in status "Success"
      |ExecutionId               |
      |{{cache:SsmExecutionId>2}}|