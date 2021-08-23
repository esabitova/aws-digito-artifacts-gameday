@ec2 @cpu @stress @integration
Feature: SSM automation document EC2 CPU stress testing
  Exercise EC2 instance CPU stress injection

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation CPU stress on EC2 instance
    Given the cached input parameters
      |AlarmGreaterThanOrEqualToThreshold|InstanceType|LoadPercent|DurationSeconds|AlarmNamespace|MetricPeriod|
      |                                70|    t2.small|         90|            180|       CWAgent|          60|
    And the cloud formation templates as integration test resources
      |CfnTemplatePath                                                                                  |ResourceType|InstanceType          |AlarmGreaterThanOrEqualToThreshold          |
      |resource_manager/cloud_formation_templates/EC2WithCWAgentCfnTemplate.yml                         |   ON_DEMAND|{{cache:InstanceType}}|{{cache:AlarmGreaterThanOrEqualToThreshold}}|
      |documents/compute/test/ec2-inject_cpu_load/2020-07-28/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE|                      |                                            |
    And published "Digito-SimulateHighCpuLoadInEc2_2020-07-28" SSM document

    When SSM automation document "Digito-SimulateHighCpuLoadInEc2_2020-07-28" executed
      |InstanceId                                         |AutomationAssumeRole                                                                |CpuUtilizationAlarmName                             |LoadPercent          |DurationSeconds          |
      |{{cfn-output:EC2WithCWAgentCfnTemplate>InstanceId}}|{{cfn-output:AutomationAssumeRoleTemplate>DigitoSimulateHighCpuLoadInEc2AssumeRole}}|{{cfn-output:EC2WithCWAgentCfnTemplate>EC2CpuAlarm}}|{{cache:LoadPercent}}|{{cache:DurationSeconds}}|
    And SSM automation document "Digito-SimulateHighCpuLoadInEc2_2020-07-28" execution in status "Success"
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|

    Then cache ssm step execution interval
      |ExecutionId               |StepName    |
      |{{cache:SsmExecutionId>1}}|RunCpuStress|
    And wait "cpu_usage_user" metric point "MORE_OR_EQUAL" to "88" "Percent"
      |StartTime                                                  |EndTime                                                  |InstanceId                                         |cpu      |Namespace               |MetricPeriod          |
      |{{cache:SsmStepExecutionInterval>1>RunCpuStress>StartTime}}|{{cache:SsmStepExecutionInterval>1>RunCpuStress>EndTime}}|{{cfn-output:EC2WithCWAgentCfnTemplate>InstanceId}}|cpu-total|{{cache:AlarmNamespace}}|{{cache:MetricPeriod}}|

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation CPU stress on EC2 instance with rollback
    Given the cached input parameters
      |AlarmGreaterThanOrEqualToThreshold|InstanceType|LoadPercent|DurationSeconds|AlarmNamespace|MetricPeriod|
      |                                70|    t2.small|         90|           1500|       CWAgent|          60|
    And the cloud formation templates as integration test resources
      |CfnTemplatePath                                                                                  |ResourceType|InstanceType          |AlarmGreaterThanOrEqualToThreshold          |
      |resource_manager/cloud_formation_templates/EC2WithCWAgentCfnTemplate.yml                         |   ON_DEMAND|{{cache:InstanceType}}|{{cache:AlarmGreaterThanOrEqualToThreshold}}|
      |documents/compute/test/ec2-inject_cpu_load/2020-07-28/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE|                      |                                            |
    And published "Digito-SimulateHighCpuLoadInEc2_2020-07-28" SSM document
    And published "Digito-KillStressCommand_2020-07-28" SSM document

    When SSM automation document "Digito-SimulateHighCpuLoadInEc2_2020-07-28" executed
      |InstanceId                                         |AutomationAssumeRole                                                                |CpuUtilizationAlarmName                             |LoadPercent          |DurationSeconds          |
      |{{cfn-output:EC2WithCWAgentCfnTemplate>InstanceId}}|{{cfn-output:AutomationAssumeRoleTemplate>DigitoSimulateHighCpuLoadInEc2AssumeRole}}|{{cfn-output:EC2WithCWAgentCfnTemplate>EC2CpuAlarm}}|{{cache:LoadPercent}}|{{cache:DurationSeconds}}|

    Then Wait for the SSM automation document "Digito-SimulateHighCpuLoadInEc2_2020-07-28" execution is on step "RunCpuStress" in status "InProgress" for "600" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And sleep for "300" seconds
    And cache ssm step execution interval
      |ExecutionId               |StepName    |
      |{{cache:SsmExecutionId>1}}|RunCpuStress|

    Then wait "cpu_usage_user" metric point "MORE_OR_EQUAL" to "88" "Percent"
      |StartTime                                                  | InstanceId                                        |cpu      |Namespace               |MetricPeriod          |
      |{{cache:SsmStepExecutionInterval>1>RunCpuStress>StartTime}}|{{cfn-output:EC2WithCWAgentCfnTemplate>InstanceId}}|cpu-total|{{cache:AlarmNamespace}}|{{cache:MetricPeriod}}|
    # Terminating SSM automation to replicate real scenario when service performs termination before executing document rollback steps.
    And terminate "Digito-SimulateHighCpuLoadInEc2_2020-07-28" SSM automation document
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|

    Then Wait for the SSM automation document "Digito-SimulateHighCpuLoadInEc2_2020-07-28" execution is on step "TriggerRollback" in status "Success" for "240" seconds
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|
    And sleep for "240" seconds

    Then SSM automation document "Digito-SimulateHighCpuLoadInEc2_2020-07-28" execution in status "Cancelled"
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|

    Then cache rollback execution id
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|

    And SSM automation document "Digito-SimulateHighCpuLoadInEc2_2020-07-28" execution in status "Success"
      |ExecutionId               |
      |{{cache:SsmExecutionId>2}}|

    Then cache ssm step execution interval
      |ExecutionId               |StepName                   |
      |{{cache:SsmExecutionId>2}}|KillStressCommandOnRollback|
    And wait "cpu_usage_user" metric point "LESS_OR_EQUAL" to "5" "Percent"
      |StartTime                                                                 |InstanceId                                         |cpu      |Namespace               |MetricPeriod          |
      |{{cache:SsmStepExecutionInterval>2>KillStressCommandOnRollback>StartTime}}|{{cfn-output:EC2WithCWAgentCfnTemplate>InstanceId}}|cpu-total|{{cache:AlarmNamespace}}|{{cache:MetricPeriod}}|
