@ec2 @memory @stress @integration
Feature: SSM automation document EC2 memory stress testing
  Exercise EC2 instance memory stress injection

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation memory stress on EC2 instance
    Given the cached input parameters
      |AlarmGreaterThanOrEqualToThreshold|InstanceType|MemoryLoadPercentage|StressDuration|AlarmNamespace|MetricPeriod|
      |                                50|    t2.small|                  90|           180|       CWAgent|          60|
    And the cloud formation templates as integration test resources
      |CfnTemplatePath                                                                                     |ResourceType|InstanceType          |AlarmGreaterThanOrEqualToThreshold          |
      |resource_manager/cloud_formation_templates/EC2WithCWAgentCfnTemplate.yml                            |   ON_DEMAND|{{cache:InstanceType}}|{{cache:AlarmGreaterThanOrEqualToThreshold}}|
      |documents/compute/test/ec2-inject_memory_load/2020-07-28/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE|                      |                                            |
    And published "Digito-SimulateHighMemoryLoadInEc2_2020-07-28" SSM document

    When SSM automation document "Digito-SimulateHighMemoryLoadInEc2_2020-07-28" executed
      |InstanceId                                         |AutomationAssumeRole                                                                   |MemoryUtilizationAlarmName                             |MemoryLoadPercentage          |Duration                |
      |{{cfn-output:EC2WithCWAgentCfnTemplate>InstanceId}}|{{cfn-output:AutomationAssumeRoleTemplate>DigitoSimulateHighMemoryLoadInEc2AssumeRole}}|{{cfn-output:EC2WithCWAgentCfnTemplate>EC2MemoryAlarm}}|{{cache:MemoryLoadPercentage}}|{{cache:StressDuration}}|
    And SSM automation document "Digito-SimulateHighMemoryLoadInEc2_2020-07-28" execution in status "Success"
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|
    # TODO(semiond): When targeting 90% memory load CW reporting ~25  bellow target, investigate: https://issues.amazon.com/issues/Digito-1767
    Then assert "mem_used_percent" metric point "greaterOrEqual" than "60" percent(s)
      |ExecutionId               |StepName       | InstanceId                                        |ImageId                                         |InstanceType          |Namespace               |MetricPeriod          |
      |{{cache:SsmExecutionId>1}}|RunMemoryStress|{{cfn-output:EC2WithCWAgentCfnTemplate>InstanceId}}|{{cfn-output:EC2WithCWAgentCfnTemplate>ImageId}}|{{cache:InstanceType}}|{{cache:AlarmNamespace}}|{{cache:MetricPeriod}}|


  Scenario: Create AWS resources using CloudFormation template and execute SSM automation memory stress on EC2 instance with rollback
    Given the cached input parameters
      |AlarmGreaterThanOrEqualToThreshold|InstanceType|MemoryLoadPercentage|StressDuration|AlarmNamespace|MetricPeriod|
      |                                50|    t2.small|                  90|           600|       CWAgent|          60|
    And the cloud formation templates as integration test resources
      |CfnTemplatePath                                                                                  |ResourceType|InstanceType          |AlarmGreaterThanOrEqualToThreshold          |
      |resource_manager/cloud_formation_templates/EC2WithCWAgentCfnTemplate.yml                         |   ON_DEMAND|{{cache:InstanceType}}|{{cache:AlarmGreaterThanOrEqualToThreshold}}|
      |documents/compute/test/ec2-inject_cpu_load/2020-07-28/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE|                      |                                            |
    And published "Digito-SimulateHighMemoryLoadInEc2_2020-07-28" SSM document
    And published "Digito-KillStressCommand_2020-07-28" SSM document

    When SSM automation document "Digito-SimulateHighMemoryLoadInEc2_2020-07-28" executed
      |InstanceId                                         |AutomationAssumeRole                                                                   |MemoryUtilizationAlarmName                             |MemoryLoadPercentage          |Duration                |
      |{{cfn-output:EC2WithCWAgentCfnTemplate>InstanceId}}|{{cfn-output:AutomationAssumeRoleTemplate>DigitoSimulateHighMemoryLoadInEc2AssumeRole}}|{{cfn-output:EC2WithCWAgentCfnTemplate>EC2MemoryAlarm}}|{{cache:MemoryLoadPercentage}}|{{cache:StressDuration}}|
    # TODO(semiond): Sleeping in order to wait for CloudWatch metrics to be available, sometimes it takes longer (~5 mins), sometimes shorter. Need to find better way to verify CPU injection.
    # https://issues.amazon.com/issues/Digito-1742
    Then sleep for "120" seconds

    When assert "mem_used_percent" metric point "greaterOrEqual" than "60" percent(s)
      |ExecutionId               |StepName       | InstanceId                                        |ImageId                                         |InstanceType          |Namespace               |MetricPeriod          |
      |{{cache:SsmExecutionId>1}}|RunMemoryStress|{{cfn-output:EC2WithCWAgentCfnTemplate>InstanceId}}|{{cfn-output:EC2WithCWAgentCfnTemplate>ImageId}}|{{cache:InstanceType}}|{{cache:AlarmNamespace}}|{{cache:MetricPeriod}}|
    Then assert SSM automation document step "RunMemoryStress" execution in status "InProgress"
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|
    # Terminating SSM automation to replicate real scenario when service performs termination before executing document rollback steps.
    And terminate "Digito-SimulateHighMemoryLoadInEc2_2020-07-28" SSM automation document
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|

    When SSM automation document "Digito-SimulateHighMemoryLoadInEc2_2020-07-28" execution in status "Cancelled"
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|
    And SSM automation document "Digito-SimulateHighMemoryLoadInEc2_2020-07-28" executed
      |AutomationAssumeRole                                                                   |IsRollback|PreviousExecutionId       |InstanceId       |MemoryUtilizationAlarmName|
      |{{cfn-output:AutomationAssumeRoleTemplate>DigitoSimulateHighMemoryLoadInEc2AssumeRole}}|      true|{{cache:SsmExecutionId>1}}|dummy-instance-id|          dummy-alarm-name|
    And SSM automation document "Digito-SimulateHighCpuLoadInEc2_2020-07-28" execution in status "Success"
      |ExecutionId               |
      |{{cache:SsmExecutionId>2}}|
    # TODO(semiond): Sleeping in order to wait for CloudWatch metrics to be available, sometimes it takes longer (~5 mins), sometimes shorter. Need to find better way to verify CPU injection.
    # https://issues.amazon.com/issues/Digito-1742
    Then sleep for "180" seconds
    And assert "mem_used_percent" metric point "less" than "10" percent(s)
      |ExecutionId               |StepName                   |InstanceId                                         |ImageId                                         |InstanceType          |Namespace               |MetricPeriod          |
      |{{cache:SsmExecutionId>2}}|KillStressCommandOnRollback|{{cfn-output:EC2WithCWAgentCfnTemplate>InstanceId}}|{{cfn-output:EC2WithCWAgentCfnTemplate>ImageId}}|{{cache:InstanceType}}|{{cache:AlarmNamespace}}|{{cache:MetricPeriod}}|