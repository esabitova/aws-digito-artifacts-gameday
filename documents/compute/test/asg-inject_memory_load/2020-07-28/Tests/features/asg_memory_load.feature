@asg @memory @stress @integration
Feature: SSM automation document ASG memory stress testing
  Exercise ASG instance memory stress injection

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document ASG memory stress
    Given the cached input parameters
      | InstanceType | MemoryLoadPercentage | StressDuration | AlarmNamespace | MetricPeriod | PercentageOfInstances | ExpectedRecoveryTime |
      | t2.small     | 90                   | 300            | CWAgent        | 60           | 50                    | 120                  |
    And the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                     | ResourceType | InstanceType           |
      | resource_manager/cloud_formation_templates/AsgCfnTemplate.yml                                       | ON_DEMAND    | {{cache:InstanceType}} |
      | documents/compute/test/asg-inject_memory_load/2020-07-28/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                        |
    And published "Digito-SimulateHighMemoryLoadInAsg_2020-07-28" SSM document

    When SSM automation document "Digito-SimulateHighMemoryLoadInAsg_2020-07-28" executed
      | AutoScalingGroupName                               | AutomationAssumeRole                                                                    | MemoryUtilizationAlarmName                                  | MemoryLoadPercentage           | Duration                 | PercentageOfInstances           | ExpectedRecoveryTime           |
      | {{cfn-output:AsgCfnTemplate>AutoScalingGroupName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoSimulateHighMemoryLoadInAsgAssumeRole}} | {{cfn-output:AsgCfnTemplate>AsgMemoryUtilizationAlarmName}} | {{cache:MemoryLoadPercentage}} | {{cache:StressDuration}} | {{cache:PercentageOfInstances}} | {{cache:ExpectedRecoveryTime}} |
    And SSM automation document "Digito-SimulateHighMemoryLoadInAsg_2020-07-28" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    Then cache ssm step execution interval
      | ExecutionId                | StepName        |
      | {{cache:SsmExecutionId>1}} | RunMemoryStress |
    And wait "mem_used_percent" metric point "MORE_OR_EQUAL" to "60" "Percent"
      | StartTime                                                      | AutoScalingGroupName                               | Namespace                | MetricPeriod           |
      | {{cache:SsmStepExecutionInterval>1>RunMemoryStress>StartTime}} | {{cfn-output:AsgCfnTemplate>AutoScalingGroupName}} | {{cache:AlarmNamespace}} | {{cache:MetricPeriod}} |

