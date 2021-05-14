@asg @cpu @stress @integration @asg_cpu_stress
Feature: SSM automation document ASG CPU stress testing
  Exercise ASG instance CPU stress injection

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation CPU stress on ASG instances
    Given the cached input parameters
      |InstanceType|CpuLoadPercentage|StressDuration|AlarmNamespace|MetricPeriod|PercentageOfInstances|ExpectedRecoveryTime|
      |    t2.small|               90|           300|       AWS/EC2|          60|                   50|                 120|
    And the cloud formation templates as integration test resources
      |CfnTemplatePath                                                                                 |ResourceType|InstanceType          |
      |resource_manager/cloud_formation_templates/AsgCfnTemplate.yml                                   |   ON_DEMAND|{{cache:InstanceType}}|
      |documents/compute/test/asg-inject_cpu_load/2020-07-28/Documents/AutomationAssumeRoleTemplate.yml| ASSUME_ROLE|                      |
    And published "Digito-SimulateHighCpuLoadInAsg_2020-07-28" SSM document

    When SSM automation document "Digito-SimulateHighCpuLoadInAsg_2020-07-28" executed
      |AutoScalingGroupName                               |AutomationAssumeRole                                                                |CpuUtilizationAlarmName                                 |CpuLoadPercentage          |Duration                |PercentageOfInstances          |ExpectedRecoveryTime          |
      |{{cfn-output:AsgCfnTemplate>AutoScalingGroupName}} |{{cfn-output:AutomationAssumeRoleTemplate>DigitoSimulateHighCpuLoadInAsgAssumeRole}}|{{cfn-output:AsgCfnTemplate>AsgCpuUtilizationAlarmName}}|{{cache:CpuLoadPercentage}}|{{cache:StressDuration}}|{{cache:PercentageOfInstances}}|{{cache:ExpectedRecoveryTime}}|
    And SSM automation document "Digito-SimulateHighCpuLoadInAsg_2020-07-28" execution in status "Success"
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|

    Then cache ssm step execution interval
      |ExecutionId               |StepName    |
      |{{cache:SsmExecutionId>1}}|RunCpuStress|
    And wait "CPUUtilization" metric point "MORE_OR_EQUAL" to "88" "Percent"
      |StartTime                                                  |AutoScalingGroupName                              |Namespace               |MetricPeriod          |
      |{{cache:SsmStepExecutionInterval>1>RunCpuStress>StartTime}}|{{cfn-output:AsgCfnTemplate>AutoScalingGroupName}}|{{cache:AlarmNamespace}}|{{cache:MetricPeriod}}|

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation CPU stress on ASG instances with rollback
    Given the cached input parameters
       |InstanceType|CpuLoadPercentage|StressDuration|AlarmNamespace|MetricPeriod|PercentageOfInstances|ExpectedRecoveryTime|
       |    t2.small|               90|           600|       AWS/EC2|          60|                   50|                 120|
    And the cloud formation templates as integration test resources
      |CfnTemplatePath                                                                                  |ResourceType|InstanceType          |
      |resource_manager/cloud_formation_templates/AsgCfnTemplate.yml                                    |   ON_DEMAND|{{cache:InstanceType}}|
      |documents/compute/test/ec2-inject_cpu_load/2020-07-28/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE|                      |
    And published "Digito-SimulateHighCpuLoadInAsg_2020-07-28" SSM document
    And published "Digito-KillStressOnHealthyInstances_2020-07-28" SSM document
    And published "Digito-KillStressCommand_2020-07-28" SSM document

    When SSM automation document "Digito-SimulateHighCpuLoadInAsg_2020-07-28" executed
      |AutoScalingGroupName                               |AutomationAssumeRole                                                                |CpuUtilizationAlarmName                                 |CpuLoadPercentage          |Duration                |PercentageOfInstances          |ExpectedRecoveryTime          |
      |{{cfn-output:AsgCfnTemplate>AutoScalingGroupName}} |{{cfn-output:AutomationAssumeRoleTemplate>DigitoSimulateHighCpuLoadInAsgAssumeRole}}|{{cfn-output:AsgCfnTemplate>AsgCpuUtilizationAlarmName}}|{{cache:CpuLoadPercentage}}|{{cache:StressDuration}}|{{cache:PercentageOfInstances}}|{{cache:ExpectedRecoveryTime}}|

    Then Wait for the SSM automation document "Digito-SimulateHighCpuLoadInAsg_2020-07-28" execution is on step "RunCpuStress" in status "InProgress" for "240" seconds
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|

    Then cache ssm step execution interval
      |ExecutionId               |StepName    |
      |{{cache:SsmExecutionId>1}}|RunCpuStress|
    And wait "CPUUtilization" metric point "MORE_OR_EQUAL" to "88" "Percent"
      |StartTime                                                  |AutoScalingGroupName                              |Namespace               |MetricPeriod          |
      |{{cache:SsmStepExecutionInterval>1>RunCpuStress>StartTime}}|{{cfn-output:AsgCfnTemplate>AutoScalingGroupName}}|{{cache:AlarmNamespace}}|{{cache:MetricPeriod}}|

    # Terminating SSM automation to replicate real scenario when service performs termination before executing document rollback steps.
    And terminate "Digito-SimulateHighCpuLoadInAsg_2020-07-28" SSM automation document
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|

    Then Wait for the SSM automation document "Digito-SimulateHighCpuLoadInAsg_2020-07-28" execution is on step "TriggerRollback" in status "Success" for "240" seconds
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|

    Then SSM automation document "Digito-SimulateHighCpuLoadInAsg_2020-07-28" execution in status "Cancelled"
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|

    Then cache rollback execution id
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|

    And SSM automation document "Digito-SimulateHighCpuLoadInAsg_2020-07-28" execution in status "Success"
      |ExecutionId               |
      |{{cache:SsmExecutionId>2}}|

    Then cache ssm step execution interval
      |ExecutionId               |StepName                   |
      |{{cache:SsmExecutionId>2}}|KillStressCommandOnRollback|
    And wait "CPUUtilization" metric point "LESS_OR_EQUAL" to "5" "Percent"
      |StartTime                                                                 |AutoScalingGroupName                              |Namespace               |MetricPeriod          |
      |{{cache:SsmStepExecutionInterval>2>KillStressCommandOnRollback>StartTime}}|{{cfn-output:AsgCfnTemplate>AutoScalingGroupName}}|{{cache:AlarmNamespace}}|{{cache:MetricPeriod}}|
