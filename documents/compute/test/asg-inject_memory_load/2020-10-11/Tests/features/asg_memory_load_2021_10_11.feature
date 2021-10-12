@asg @memory @stress @integration
Feature: SSM automation document ASG memory stress testing
  Exercise ASG instance memory stress injection

  Scenario: Execute SSM automation document to perform memory stress injection on ASG
    Given the cached input parameters
      | InstanceType | LoadPercent | DurationSeconds | AlarmNamespace | MetricPeriod | PercentageOfInstances | ExpectedRecoveryTime | Workers |
      | t2.small     | 90          | 300             | CWAgent        | 60           | 50                    | 120                  | 6       |
    And the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                     | ResourceType | InstanceType           |
      | resource_manager/cloud_formation_templates/AsgCfnTemplate.yml                                       | ON_DEMAND    | {{cache:InstanceType}} |
      | documents/compute/test/asg-inject_memory_load/2020-10-11/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                        |
    And published "Digito-InjectMemoryLoadInAsgTest_2020-10-11" SSM document

    When SSM automation document "Digito-InjectMemoryLoadInAsgTest_2020-10-11" executed
      | AutoScalingGroupName                               | AutomationAssumeRole                                                                    | MemoryUtilizationAlarmName                                  | LoadPercent           | DurationSeconds           | PercentageOfInstances           | ExpectedRecoveryTime           |Workers          |
      | {{cfn-output:AsgCfnTemplate>AutoScalingGroupName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoSimulateHighMemoryLoadInAsgAssumeRole}} | {{cfn-output:AsgCfnTemplate>AsgMemoryUtilizationAlarmName}} | {{cache:LoadPercent}} | {{cache:DurationSeconds}} | {{cache:PercentageOfInstances}} | {{cache:ExpectedRecoveryTime}} |{{cache:Workers}}|
    And SSM automation document "Digito-InjectMemoryLoadInAsgTest_2020-10-11" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    Then cache ssm step execution interval
      | ExecutionId                | StepName        |
      | {{cache:SsmExecutionId>1}} | RunMemoryStress |
    And wait "mem_used_percent" metric point "MORE_OR_EQUAL" to "60" "Percent"
      | StartTime                                                      | AutoScalingGroupName                               | Namespace                | MetricPeriod           |
      | {{cache:SsmStepExecutionInterval>1>RunMemoryStress>StartTime}} | {{cfn-output:AsgCfnTemplate>AutoScalingGroupName}} | {{cache:AlarmNamespace}} | {{cache:MetricPeriod}} |


  Scenario: Execute SSM automation document to perform memory stress injection on ASG with rollback
    Given the cached input parameters
      | InstanceType | LoadPercent | DurationSeconds | AlarmNamespace | MetricPeriod | PercentageOfInstances | ExpectedRecoveryTime | Workers |
      | t2.small     | 90          | 900             | CWAgent        | 60           | 50                    | 120                  | 6       |
    And the cloud formation templates as integration test resources
      |CfnTemplatePath                                                                                     |ResourceType|InstanceType          |
      |resource_manager/cloud_formation_templates/AsgCfnTemplate.yml                                       |   ON_DEMAND|{{cache:InstanceType}}|
      |documents/compute/test/asg-inject_memory_load/2020-10-11/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE|                      |
    And published "Digito-InjectMemoryLoadInAsgTest_2020-10-11" SSM document

    When SSM automation document "Digito-InjectMemoryLoadInAsgTest_2020-10-11" executed
      | AutoScalingGroupName                               | AutomationAssumeRole                                                                    | MemoryUtilizationAlarmName                                  | LoadPercent           | DurationSeconds           | PercentageOfInstances           | ExpectedRecoveryTime           |Workers          |
      | {{cfn-output:AsgCfnTemplate>AutoScalingGroupName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoSimulateHighMemoryLoadInAsgAssumeRole}} | {{cfn-output:AsgCfnTemplate>AsgMemoryUtilizationAlarmName}} | {{cache:LoadPercent}} | {{cache:DurationSeconds}} | {{cache:PercentageOfInstances}} | {{cache:ExpectedRecoveryTime}} |{{cache:Workers}}|

    Then Wait for the SSM automation document "Digito-InjectMemoryLoadInAsgTest_2020-10-11" execution is on step "RunMemoryStress" in status "InProgress" for "600" seconds
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|
    And sleep for "300" seconds

    Then cache ssm step execution interval
      |ExecutionId               |StepName    |
      |{{cache:SsmExecutionId>1}}|RunMemoryStress|
    And wait "mem_used_percent" metric point "MORE_OR_EQUAL" to "60" "Percent"
      |StartTime                                                     |AutoScalingGroupName                              |Namespace               |MetricPeriod          |
      |{{cache:SsmStepExecutionInterval>1>RunMemoryStress>StartTime}}|{{cfn-output:AsgCfnTemplate>AutoScalingGroupName}}|{{cache:AlarmNamespace}}|{{cache:MetricPeriod}}|

    # Terminating SSM automation to replicate real scenario when service performs termination before executing document rollback steps.
    And terminate "Digito-InjectMemoryLoadInAsgTest_2020-10-11" SSM automation document
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|

    Then Wait for the SSM automation document "Digito-InjectMemoryLoadInAsgTest_2020-10-11" execution is on step "TriggerRollback" in status "Success" for "240" seconds
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|

    Then SSM automation document "Digito-InjectMemoryLoadInAsgTest_2020-10-11" execution in status "Cancelled"
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|

    Then cache rollback execution id
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|

    And SSM automation document "Digito-InjectMemoryLoadInAsgTest_2020-10-11" execution in status "Success"
      |ExecutionId               |
      |{{cache:SsmExecutionId>2}}|

    Then cache ssm step execution interval
      |ExecutionId               |StepName                   |
      |{{cache:SsmExecutionId>2}}|KillStressCommandOnRollback|
    And wait "mem_used_percent" metric point "LESS_OR_EQUAL" to "5" "Percent"
      |StartTime                                                                 |AutoScalingGroupName                              |Namespace               |MetricPeriod          |
      |{{cache:SsmStepExecutionInterval>2>KillStressCommandOnRollback>StartTime}}|{{cfn-output:AsgCfnTemplate>AutoScalingGroupName}}|{{cache:AlarmNamespace}}|{{cache:MetricPeriod}}|
