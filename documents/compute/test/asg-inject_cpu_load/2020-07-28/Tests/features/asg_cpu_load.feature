@asg @cpu @stress @integration @asg_cpu_stress
Feature: SSM automation document ASG CPU stress testing
  Exercise ASG instance CPU stress injection

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation CPU stress on ASG instances
    Given the cached input parameters
      |InstanceType|CpuLoadPercentage|StressDuration|AlarmNamespace|MetricPeriod|PercentageOfInstances|ExpectedRecoveryTime|
      |    t2.small|               90|           180|       AWS/EC2|          60|                   50|                 120|
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

    Then sleep for "120" seconds
    And assert "CPUUtilization" metric point "greaterOrEqual" than "88" percent(s)
      |ExecutionId               |StepName    |AutoScalingGroupName                              |Namespace               |MetricPeriod          |
      |{{cache:SsmExecutionId>1}}|RunCpuStress|{{cfn-output:AsgCfnTemplate>AutoScalingGroupName}}|{{cache:AlarmNamespace}}|{{cache:MetricPeriod}}|

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation CPU stress on ASG instances with rollback
    Given the cached input parameters
       |InstanceType|CpuLoadPercentage|StressDuration|AlarmNamespace|MetricPeriod|PercentageOfInstances|ExpectedRecoveryTime|
       |    t2.small|               90|           600|       AWS/EC2|          60|                   50|                 120|
    And the cloud formation templates as integration test resources
      |CfnTemplatePath                                                                                  |ResourceType|InstanceType          |
      |resource_manager/cloud_formation_templates/AsgCfnTemplate.yml                                    |   ON_DEMAND|{{cache:InstanceType}}|
      |documents/compute/test/ec2-inject_cpu_load/2020-07-28/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE|                      |
    And published "Digito-SimulateHighCpuLoadInAsg_2020-07-28" SSM document

    When SSM automation document "Digito-SimulateHighCpuLoadInAsg_2020-07-28" executed
      |AutoScalingGroupName                               |AutomationAssumeRole                                                                |CpuUtilizationAlarmName                                 |CpuLoadPercentage          |Duration                |PercentageOfInstances          |ExpectedRecoveryTime          |
      |{{cfn-output:AsgCfnTemplate>AutoScalingGroupName}} |{{cfn-output:AutomationAssumeRoleTemplate>DigitoSimulateHighCpuLoadInAsgAssumeRole}}|{{cfn-output:AsgCfnTemplate>AsgCpuUtilizationAlarmName}}|{{cache:CpuLoadPercentage}}|{{cache:StressDuration}}|{{cache:PercentageOfInstances}}|{{cache:ExpectedRecoveryTime}}|
    # TODO(semiond): Sleeping in order to wait for CloudWatch metrics to be available, sometimes it takes longer, sometimes shorter. Need to find better way to verify CPU injection.
    # https://issues.amazon.com/issues/Digito-1742
    Then sleep for "180" seconds
    And assert "CPUUtilization" metric point "greaterOrEqual" than "88" percent(s)
      |ExecutionId               |StepName    |AutoScalingGroupName                              |Namespace               |MetricPeriod          |
      |{{cache:SsmExecutionId>1}}|RunCpuStress|{{cfn-output:AsgCfnTemplate>AutoScalingGroupName}}|{{cache:AlarmNamespace}}|{{cache:MetricPeriod}}|

    Then assert SSM automation document step "RunCpuStress" execution in status "InProgress"
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|
    # Terminating SSM automation to replicate real scenario when service performs termination before executing document rollback steps.
    And terminate "Digito-SimulateHighCpuLoadInAsg_2020-07-28" SSM automation document
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|

    When SSM automation document "Digito-SimulateHighCpuLoadInAsg_2020-07-28" execution in status "Cancelled"
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|
    And SSM automation document "Digito-SimulateHighCpuLoadInAsg_2020-07-28" executed
      |AutoScalingGroupName                               |AutomationAssumeRole                                                                |IsRollback|PreviousExecutionId       |CpuUtilizationAlarmName|
      |{{cfn-output:AsgCfnTemplate>AutoScalingGroupName}} |{{cfn-output:AutomationAssumeRoleTemplate>DigitoSimulateHighCpuLoadInAsgAssumeRole}}|true      |{{cache:SsmExecutionId>1}}|dummy-alarm-name       |
    And SSM automation document "Digito-SimulateHighCpuLoadInAsg_2020-07-28" execution in status "Success"
      |ExecutionId               |
      |{{cache:SsmExecutionId>2}}|
    # TODO(semiond): Sleeping in order to wait for CloudWatch metrics to be available, sometimes it takes longer, sometimes shorter. Need to find better way to verify CPU injection.
    # https://issues.amazon.com/issues/Digito-1742
    Then sleep for "180" seconds
    And assert "CPUUtilization" metric point "less" than "5" percent(s)
      |ExecutionId               |StepName                   |AutoScalingGroupName                              |Namespace               |MetricPeriod          |
      |{{cache:SsmExecutionId>2}}|KillStressCommandOnRollback|{{cfn-output:AsgCfnTemplate>AutoScalingGroupName}}|{{cache:AlarmNamespace}}|{{cache:MetricPeriod}}|



