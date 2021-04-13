@ec2 @cpu @stress @integration
Feature: SSM automation document EC2 CPU stress testing
  Exercise EC2 instance CPU stress injection

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation CPU stress on EC2 instance
    Given the cached input parameters
      |AlarmGreaterThanOrEqualToThreshold|InstanceType|CpuLoadPercentage|StressDuration|AlarmNamespace|MetricPeriod|
      |                                70|    t2.small|               90|           180|       CWAgent|          60|
    And the cloud formation templates as integration test resources
      |CfnTemplatePath                                                                                  |ResourceType|InstanceType          |AlarmGreaterThanOrEqualToThreshold          |
      |resource_manager/cloud_formation_templates/EC2WithCWAgentCfnTemplate.yml                         |   ON_DEMAND|{{cache:InstanceType}}|{{cache:AlarmGreaterThanOrEqualToThreshold}}|
      |documents/compute/test/ec2-inject_cpu_load/2020-07-28/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE|                      |                                            |
    And published "Digito-SimulateHighCpuLoadInEc2_2020-07-28" SSM document

    When SSM automation document "Digito-SimulateHighCpuLoadInEc2_2020-07-28" executed
      |InstanceId                                         |AutomationAssumeRole                                                                |CpuUtilizationAlarmName                             |CpuLoadPercentage          |Duration                |
      |{{cfn-output:EC2WithCWAgentCfnTemplate>InstanceId}}|{{cfn-output:AutomationAssumeRoleTemplate>DigitoSimulateHighCpuLoadInEc2AssumeRole}}|{{cfn-output:EC2WithCWAgentCfnTemplate>EC2CpuAlarm}}|{{cache:CpuLoadPercentage}}|{{cache:StressDuration}}|
    And SSM automation document "Digito-SimulateHighCpuLoadInEc2_2020-07-28" execution in status "Success"
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|

    Then sleep for "120" seconds
    And assert "cpu_usage_user" metric point "greaterOrEqual" than "88" percent(s)
      |ExecutionId               |StepName    | InstanceId                                        |ImageId                                         |InstanceType          |cpu      |Namespace               |MetricPeriod          |
      |{{cache:SsmExecutionId>1}}|RunCpuStress|{{cfn-output:EC2WithCWAgentCfnTemplate>InstanceId}}|{{cfn-output:EC2WithCWAgentCfnTemplate>ImageId}}|{{cache:InstanceType}}|cpu-total|{{cache:AlarmNamespace}}|{{cache:MetricPeriod}}|

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation CPU stress on EC2 instance with rollback
    Given the cached input parameters
      |AlarmGreaterThanOrEqualToThreshold|InstanceType|CpuLoadPercentage|StressDuration|AlarmNamespace|MetricPeriod|
      |                                70|    t2.small|               90|          1500|       CWAgent|          60|
    And the cloud formation templates as integration test resources
      |CfnTemplatePath                                                                                  |ResourceType|InstanceType          |AlarmGreaterThanOrEqualToThreshold          |
      |resource_manager/cloud_formation_templates/EC2WithCWAgentCfnTemplate.yml                         |   ON_DEMAND|{{cache:InstanceType}}|{{cache:AlarmGreaterThanOrEqualToThreshold}}|
      |documents/compute/test/ec2-inject_cpu_load/2020-07-28/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE|                      |                                            |
    And published "Digito-SimulateHighCpuLoadInEc2_2020-07-28" SSM document
    And published "Digito-KillStressCommand_2020-07-28" SSM document

    When SSM automation document "Digito-SimulateHighCpuLoadInEc2_2020-07-28" executed
      |InstanceId                                         |AutomationAssumeRole                                                                |CpuUtilizationAlarmName                             |CpuLoadPercentage          |Duration                |
      |{{cfn-output:EC2WithCWAgentCfnTemplate>InstanceId}}|{{cfn-output:AutomationAssumeRoleTemplate>DigitoSimulateHighCpuLoadInEc2AssumeRole}}|{{cfn-output:EC2WithCWAgentCfnTemplate>EC2CpuAlarm}}|{{cache:CpuLoadPercentage}}|{{cache:StressDuration}}|
    # TODO(semiond): Sleeping in order to wait for CloudWatch metrics to be available, sometimes it takes longer, sometimes shorter. Need to find better way to verify CPU injection.
    # https://issues.amazon.com/issues/Digito-1742
    Then sleep for "180" seconds

    When assert "cpu_usage_user" metric point "greaterOrEqual" than "88" percent(s)
      |ExecutionId               |StepName    | InstanceId                                        |ImageId                                         |InstanceType          |cpu      |Namespace               |MetricPeriod          |
      |{{cache:SsmExecutionId>1}}|RunCpuStress|{{cfn-output:EC2WithCWAgentCfnTemplate>InstanceId}}|{{cfn-output:EC2WithCWAgentCfnTemplate>ImageId}}|{{cache:InstanceType}}|cpu-total|{{cache:AlarmNamespace}}|{{cache:MetricPeriod}}|
    Then assert SSM automation document step "RunCpuStress" execution in status "InProgress"
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|
    # Terminating SSM automation to replicate real scenario when service performs termination before executing document rollback steps.
    And terminate "Digito-SimulateHighCpuLoadInEc2_2020-07-28" SSM automation document
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|

    When SSM automation document "Digito-SimulateHighCpuLoadInEc2_2020-07-28" execution in status "Cancelled"
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|
    And SSM automation document "Digito-SimulateHighCpuLoadInEc2_2020-07-28" executed
      |AutomationAssumeRole                                                                |IsRollback|PreviousExecutionId       |InstanceId       |CpuUtilizationAlarmName|
      |{{cfn-output:AutomationAssumeRoleTemplate>DigitoSimulateHighCpuLoadInEc2AssumeRole}}|      true|{{cache:SsmExecutionId>1}}|dummy-instance-id|       dummy-alarm-name|
    And SSM automation document "Digito-SimulateHighCpuLoadInEc2_2020-07-28" execution in status "Success"
      |ExecutionId               |
      |{{cache:SsmExecutionId>2}}|
    # TODO(semiond): Sleeping in order to wait for CloudWatch metrics to be available, sometimes it takes longer, sometimes shorter. Need to find better way to verify CPU injection.
    # https://issues.amazon.com/issues/Digito-1742
    Then sleep for "180" seconds
    And assert "cpu_usage_user" metric point "less" than "5" percent(s)
      |ExecutionId               |StepName                   |InstanceId                                         |ImageId                                         |InstanceType          |Namespace               |MetricPeriod          |
      |{{cache:SsmExecutionId>2}}|KillStressCommandOnRollback|{{cfn-output:EC2WithCWAgentCfnTemplate>InstanceId}}|{{cfn-output:EC2WithCWAgentCfnTemplate>ImageId}}|{{cache:InstanceType}}|{{cache:AlarmNamespace}}|{{cache:MetricPeriod}}|




