@ec2 @integration @kill_process
Feature: SSM automation document EC2 CPU kill process document testing

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation to kill process on ec2 instance
    Given the cached input parameters
      |AlarmOnGreaterThenThreshold|InstanceType|ProcessName|
      |                         70|    t2.small|      httpd|
    And the cloud formation templates as integration test resources
      |CfnTemplatePath                                                                                        |ResourceType|InstanceType          |AlarmOnGreaterThenThreshold          |
      |resource_manager/cloud_formation_templates/Ec2InstanceCfnTemplate.yml                                  |   ON_DEMAND|{{cache:InstanceType}}|{{cache:AlarmOnGreaterThenThreshold}}|
      |documents/stateless-compute/test/ec2-kill_process/2020-07-28/Documents/AutomationAssumeRoleTemplate.yml| ASSUME_ROLE|                      |                                     |
    And SSM automation document "AWS-RestartEC2Instance" executed
      |                                      InstanceId|
      |{{cfn-output:Ec2InstanceCfnTemplate>InstanceId}}|
    And SSM automation document "AWS-RestartEC2Instance" execution in status "Success"
      |               ExecutionId|
      |{{cache:SsmExecutionId>1}}|

    When SSM automation document "Digito-KillProcessEc2_2020-07-28" executed
      |InstanceId                                      |AutomationAssumeRole                                                      |SyntheticAlarmName                                           |ProcessName          |
      |{{cfn-output:Ec2InstanceCfnTemplate>InstanceId}}|{{cfn-output:AutomationAssumeRoleTemplate>DigitoKillProcessEc2AssumeRole}}|{{cfn-output:Ec2InstanceCfnTemplate>CpuUtilizationAlarmName}}|{{cache:ProcessName}}|

    Then SSM automation document "Digito-KillProcessEc2_2020-07-28" execution in status "Success"
      |ExecutionId               |
      |{{cache:SsmExecutionId>2}}|

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation to kill process on ec2 instance, process does not exist
    Given the cached input parameters
      |AlarmOnGreaterThenThreshold|InstanceType|         ProcessName|
      |                         70|    t2.small|non_existing_process|
    And the cloud formation templates as integration test resources
      |CfnTemplatePath                                                                                            |ResourceType|InstanceType          |AlarmOnGreaterThenThreshold          |
      |resource_manager/cloud_formation_templates/Ec2InstanceCfnTemplate.yml                                      |   ON_DEMAND|{{cache:InstanceType}}|{{cache:AlarmOnGreaterThenThreshold}}|
      |documents/stateless-compute/test/ec2-kill_process/2020-07-28/Documents/AutomationAssumeRoleTemplate.yml    | ASSUME_ROLE|                      |                                     |

    When SSM automation document "Digito-KillProcessEc2_2020-07-28" executed
      |InstanceId                                      |AutomationAssumeRole                                                      |SyntheticAlarmName                                           |ProcessName          |
      |{{cfn-output:Ec2InstanceCfnTemplate>InstanceId}}|{{cfn-output:AutomationAssumeRoleTemplate>DigitoKillProcessEc2AssumeRole}}|{{cfn-output:Ec2InstanceCfnTemplate>CpuUtilizationAlarmName}}|{{cache:ProcessName}}|

    Then SSM automation document "Digito-KillProcessEc2_2020-07-28" execution in status "Failed"
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|