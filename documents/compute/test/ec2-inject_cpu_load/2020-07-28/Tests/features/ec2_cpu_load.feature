@ec2 @cpu @stress @integration
Feature: SSM automation document EC2 CPU stress testing
  Exercise EC2 instance CPU stress injection

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation CPU stress on EC2 instance
    Given the cached input parameters
      |AlarmOnGreaterThenThreshold|InstanceType|CpuLoadPercentage|StressDuration|
      |                         70|    t2.small|               90|           300|
    And the cloud formation templates as integration test resources
      |CfnTemplatePath                                                                                            |ResourceType|InstanceType          |AlarmOnGreaterThenThreshold          |
      |resource_manager/cloud_formation_templates/Ec2InstanceCfnTemplate.yml                                      |   ON_DEMAND|{{cache:InstanceType}}|{{cache:AlarmOnGreaterThenThreshold}}|
      |documents/compute/test/ec2-inject_cpu_load/2020-07-28/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE|                      |                                     |
    And SSM automation document "Digito-SimulateHighCpuLoadInEc2_2020-07-28" executed
      |InstanceId                                      |AutomationAssumeRole                                                                |CpuUtilizationAlarmName                                      |CpuLoadPercentage          |Duration                |
      |{{cfn-output:Ec2InstanceCfnTemplate>InstanceId}}|{{cfn-output:AutomationAssumeRoleTemplate>DigitoSimulateHighCpuLoadInEc2AssumeRole}}|{{cfn-output:Ec2InstanceCfnTemplate>CpuUtilizationAlarmName}}|{{cache:CpuLoadPercentage}}|{{cache:StressDuration}}|

    When SSM automation document "Digito-SimulateHighCpuLoadInEc2_2020-07-28" execution in status "Success"
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|
    Then assert "CPUUtilization" metric reached "88" percent(s)
      |InstanceId                                      |ExecutionId               |
      |{{cfn-output:Ec2InstanceCfnTemplate>InstanceId}}|{{cache:SsmExecutionId>1}}|

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation CPU stress on EC2 instance with rollback
    Given the cached input parameters
      |AlarmOnGreaterThenThreshold|InstanceType|CpuLoadPercentage|StressDuration|
      |                         70|    t2.small|               90|          1500|
    And the cloud formation templates as integration test resources
      |CfnTemplatePath                                                                                            |ResourceType|InstanceType          |AlarmOnGreaterThenThreshold          |
      |resource_manager/cloud_formation_templates/Ec2InstanceCfnTemplate.yml                                      |   ON_DEMAND|{{cache:InstanceType}}|{{cache:AlarmOnGreaterThenThreshold}}|
      |documents/compute/test/ec2-inject_cpu_load/2020-07-28/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE|                      |                                     |
    And SSM automation document "Digito-SimulateHighCpuLoadInEc2_2020-07-28" executed
      |InstanceId                                      |AutomationAssumeRole                                                                |CpuUtilizationAlarmName                                      |CpuLoadPercentage          |Duration                |
      |{{cfn-output:Ec2InstanceCfnTemplate>InstanceId}}|{{cfn-output:AutomationAssumeRoleTemplate>DigitoSimulateHighCpuLoadInEc2AssumeRole}}|{{cfn-output:Ec2InstanceCfnTemplate>CpuUtilizationAlarmName}}|{{cache:CpuLoadPercentage}}|{{cache:StressDuration}}|
    # TODO(semiond): Sleeping in order to wait for CloudWatch metrics to be available, sometimes it takes longer (~5 mins), sometimes shorter. Need to find better way to verify CPU injection.
    # https://issues.amazon.com/issues/Digito-1742
    Then sleep for "420" seconds

    When assert "CPUUtilization" metric reached "88" percent(s)
      |InstanceId                                      |ExecutionId               |
      |{{cfn-output:Ec2InstanceCfnTemplate>InstanceId}}|{{cache:SsmExecutionId>1}}|
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
    # TODO(semiond): Sleeping in order to wait for CloudWatch metrics to be available, sometimes it takes longer (~5 mins), sometimes shorter. Need to find better way to verify CPU injection.
    # https://issues.amazon.com/issues/Digito-1742
    Then sleep for "600" seconds
    And assert "CPUUtilization" metric below "5" percent(s) after rollback
      |InstanceId                                      |ExecutionId               |RollbackExecutionId       |
      |{{cfn-output:Ec2InstanceCfnTemplate>InstanceId}}|{{cache:SsmExecutionId>1}}|{{cache:SsmExecutionId>2}}|




