@ec2 @network_unavailable @integration
Feature: SSM automation document EC2 Network Unavailable testing
  Exercise EC2 instance Network Unavailable injection

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation network unavailable on EC2 instance
    Given the cached input parameters
      |AlarmGreaterThanOrEqualToThreshold|InstanceType|DurationInMinutes|
      |                                70|    t2.small|                10|
    And the cloud formation templates as integration test resources
      |CfnTemplatePath                                                                                  |ResourceType|InstanceType          |AlarmGreaterThanOrEqualToThreshold          |
      |resource_manager/cloud_formation_templates/EC2WithCWAgentCfnTemplate.yml                         |   ON_DEMAND|{{cache:InstanceType}}|{{cache:AlarmGreaterThanOrEqualToThreshold}}|
      |documents/compute/test/ec2-network_unavailable/2020-07-23/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE|                      |                                            |
    And published "Digito-SimulateNetworkUnavailableInEc2_2020-07-23" SSM document

    When SSM automation document "Digito-SimulateNetworkUnavailableInEc2_2020-07-23" executed
      |InstanceId                                         |AutomationAssumeRole                                                                       |SyntheticAlarmName                                  |DurationInMinutes          |
      |{{cfn-output:EC2WithCWAgentCfnTemplate>InstanceId}}|{{cfn-output:AutomationAssumeRoleTemplate>DigitoSimulateNetworkUnavailableInEc2AssumeRole}}|{{cfn-output:EC2WithCWAgentCfnTemplate>EC2CpuAlarm}}|{{cache:DurationInMinutes}}|

    Then SSM automation document "Digito-SimulateNetworkUnavailableInEc2_2020-07-23" execution in status "Success"
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation network unavailable on EC2 instance in rollback mode
    Given the cached input parameters
      |AlarmGreaterThanOrEqualToThreshold|InstanceType|DurationInMinutes|
      |                                70|    t2.small|                10|
    And the cloud formation templates as integration test resources
      |CfnTemplatePath                                                                                  |ResourceType|InstanceType          |AlarmGreaterThanOrEqualToThreshold          |
      |resource_manager/cloud_formation_templates/EC2WithCWAgentCfnTemplate.yml                         |   ON_DEMAND|{{cache:InstanceType}}|{{cache:AlarmGreaterThanOrEqualToThreshold}}|
      |documents/compute/test/ec2-network_unavailable/2020-07-23/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE|                      |                                            |
    And published "Digito-SimulateNetworkUnavailableInEc2_2020-07-23" SSM document

    When SSM automation document "Digito-SimulateNetworkUnavailableInEc2_2020-07-23" executed
      |InstanceId                                         |AutomationAssumeRole                                                                       |SyntheticAlarmName                                  |DurationInMinutes          |
      |{{cfn-output:EC2WithCWAgentCfnTemplate>InstanceId}}|{{cfn-output:AutomationAssumeRoleTemplate>DigitoSimulateNetworkUnavailableInEc2AssumeRole}}|{{cfn-output:EC2WithCWAgentCfnTemplate>EC2CpuAlarm}}|{{cache:DurationInMinutes}}|

    Then sleep for "90" seconds

    Then assert SSM automation document step "WaitForTestDuration" execution in status "InProgress"
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|

    And terminate "Digito-SimulateNetworkUnavailableInEc2_2020-07-23" SSM automation document
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|

    When SSM automation document "Digito-SimulateNetworkUnavailableInEc2_2020-07-23" execution in status "Cancelled"
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|
    And SSM automation document "Digito-SimulateNetworkUnavailableInEc2_2020-07-23" executed
      |InstanceId                                         |AutomationAssumeRole                                                                       |SyntheticAlarmName                                  |DurationInMinutes          |IsRollback|PreviousExecutionId       |
      |{{cfn-output:EC2WithCWAgentCfnTemplate>InstanceId}}|{{cfn-output:AutomationAssumeRoleTemplate>DigitoSimulateNetworkUnavailableInEc2AssumeRole}}|{{cfn-output:EC2WithCWAgentCfnTemplate>EC2CpuAlarm}}|{{cache:DurationInMinutes}}|      true|{{cache:SsmExecutionId>1}}|

    Then SSM automation document "Digito-SimulateNetworkUnavailableInEc2_2020-07-23" execution in status "Success"
      |ExecutionId               |
      |{{cache:SsmExecutionId>2}}|

    And assert SSM automation document step "RebootInstancePreviousExecution" execution in status "Success"
      |ExecutionId               |
      |{{cache:SsmExecutionId>2}}|
