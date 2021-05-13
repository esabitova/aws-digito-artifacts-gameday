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
    And published "Digito-KillStressCommand_2020-07-28" SSM document

    When SSM automation document "Digito-SimulateHighMemoryLoadInEc2_2020-07-28" executed
      |InstanceId                                         |AutomationAssumeRole                                                                   |MemoryUtilizationAlarmName                             |MemoryLoadPercentage          |DurationSeconds         |
      |{{cfn-output:EC2WithCWAgentCfnTemplate>InstanceId}}|{{cfn-output:AutomationAssumeRoleTemplate>DigitoSimulateHighMemoryLoadInEc2AssumeRole}}|{{cfn-output:EC2WithCWAgentCfnTemplate>EC2MemoryAlarm}}|{{cache:MemoryLoadPercentage}}|{{cache:StressDuration}}|
    And SSM automation document "Digito-SimulateHighMemoryLoadInEc2_2020-07-28" execution in status "Success"
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|

    Then cache ssm step execution interval
      |ExecutionId               |StepName       |
      |{{cache:SsmExecutionId>1}}|RunMemoryStress|
    # TODO(semiond): When targeting 90% memory load CW reporting ~35  bellow target, investigate: https://issues.amazon.com/issues/Digito-1767
    And wait "mem_used_percent" metric point "MORE_OR_EQUAL" to "50" "Percent"
      |StartTime                                                     |EndTime                                                     |InstanceId                                         |ImageId                                         |InstanceType          |Namespace               |MetricPeriod          |
      |{{cache:SsmStepExecutionInterval>1>RunMemoryStress>StartTime}}|{{cache:SsmStepExecutionInterval>1>RunMemoryStress>EndTime}}|{{cfn-output:EC2WithCWAgentCfnTemplate>InstanceId}}|{{cfn-output:EC2WithCWAgentCfnTemplate>ImageId}}|{{cache:InstanceType}}|{{cache:AlarmNamespace}}|{{cache:MetricPeriod}}|


  Scenario: Create AWS resources using CloudFormation template and execute SSM automation memory stress on EC2 instance with rollback
    Given the cached input parameters
      |AlarmGreaterThanOrEqualToThreshold|InstanceType|MemoryLoadPercentage|StressDuration|AlarmNamespace|MetricPeriod|
      |                                50|    t2.small|                  90|           600|       CWAgent|          60|
    And the cloud formation templates as integration test resources
      |CfnTemplatePath                                                                                    |ResourceType|InstanceType          |AlarmGreaterThanOrEqualToThreshold          |
      |resource_manager/cloud_formation_templates/EC2WithCWAgentCfnTemplate.yml                           |   ON_DEMAND|{{cache:InstanceType}}|{{cache:AlarmGreaterThanOrEqualToThreshold}}|
      |documents/compute/test/ec2-inject_memory_load/2020-07-28/Documents/AutomationAssumeRoleTemplate.yml| ASSUME_ROLE|                      |                                            |
    And published "Digito-SimulateHighMemoryLoadInEc2_2020-07-28" SSM document
    And published "Digito-KillStressCommand_2020-07-28" SSM document

    When SSM automation document "Digito-SimulateHighMemoryLoadInEc2_2020-07-28" executed
      |InstanceId                                         |AutomationAssumeRole                                                                   |MemoryUtilizationAlarmName                             |MemoryLoadPercentage          |DurationSeconds         |
      |{{cfn-output:EC2WithCWAgentCfnTemplate>InstanceId}}|{{cfn-output:AutomationAssumeRoleTemplate>DigitoSimulateHighMemoryLoadInEc2AssumeRole}}|{{cfn-output:EC2WithCWAgentCfnTemplate>EC2MemoryAlarm}}|{{cache:MemoryLoadPercentage}}|{{cache:StressDuration}}|

    Then Wait for the SSM automation document "Digito-SimulateHighMemoryLoadInEc2_2020-07-28" execution is on step "RunMemoryStress" in status "InProgress" for "600" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache ssm step execution interval
      |ExecutionId               |StepName       |
      |{{cache:SsmExecutionId>1}}|RunMemoryStress|

    # TODO(semiond): When targeting 90% memory load CW reporting ~35  bellow target, investigate: https://issues.amazon.com/issues/Digito-1767
    Then wait "mem_used_percent" metric point "MORE_OR_EQUAL" to "50" "Percent"
      |StartTime                                                     | InstanceId                                        |ImageId                                         |InstanceType          |Namespace               |MetricPeriod          |
      |{{cache:SsmStepExecutionInterval>1>RunMemoryStress>StartTime}}|{{cfn-output:EC2WithCWAgentCfnTemplate>InstanceId}}|{{cfn-output:EC2WithCWAgentCfnTemplate>ImageId}}|{{cache:InstanceType}}|{{cache:AlarmNamespace}}|{{cache:MetricPeriod}}|

    # Terminating SSM automation to replicate real scenario when service performs termination before executing document rollback steps.
    And terminate "Digito-SimulateHighMemoryLoadInEc2_2020-07-28" SSM automation document
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|

    Then Wait for the SSM automation document "Digito-SimulateHighMemoryLoadInEc2_2020-07-28" execution is on step "TriggerRollback" in status "Success" for "240" seconds
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|

    Then SSM automation document "Digito-SimulateHighMemoryLoadInEc2_2020-07-28" execution in status "Cancelled"
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|

    Then cache rollback execution id
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|

    And SSM automation document "Digito-SimulateHighMemoryLoadInEc2_2020-07-28" execution in status "Success"
      |ExecutionId               |
      |{{cache:SsmExecutionId>2}}|

    Then cache ssm step execution interval
      |ExecutionId               |StepName                   |
      |{{cache:SsmExecutionId>2}}|KillStressCommandOnRollback|

    And wait "mem_used_percent" metric point "LESS_OR_EQUAL" to "10" "Percent"
      |StartTime                                                                 |InstanceId                                         |ImageId                                         |InstanceType          |Namespace               |MetricPeriod          |
      |{{cache:SsmStepExecutionInterval>2>KillStressCommandOnRollback>StartTime}}|{{cfn-output:EC2WithCWAgentCfnTemplate>InstanceId}}|{{cfn-output:EC2WithCWAgentCfnTemplate>ImageId}}|{{cache:InstanceType}}|{{cache:AlarmNamespace}}|{{cache:MetricPeriod}}|
