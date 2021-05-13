@asg @integration @asg_az_outage
Feature: SSM automation document ASG AZ outage testing
  Exercise ASG az outage injection

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation AZ outage on ASG instances
    Given the cached input parameters
      |InstanceType|TestDurationInMinutes|
      |    t2.small|                    5|
    And the cloud formation templates as integration test resources
      |CfnTemplatePath                                                                                          |ResourceType|InstanceType          |
      |resource_manager/cloud_formation_templates/AsgCfnTemplate.yml                                            |   ON_DEMAND|{{cache:InstanceType}}|
      |documents/compute/test/asg-availability_zone_outage/2020-07-23/Documents/AutomationAssumeRoleTemplate.yml| ASSUME_ROLE|                      |
    And published "Digito-SimulateAzOutageInAsg_2020-07-23" SSM document

    When SSM automation document "Digito-SimulateAzOutageInAsg_2020-07-23" executed
      |AutoScalingGroupName                               |AutomationAssumeRole                                                             |SyntheticAlarmName                          |TestDurationInMinutes          |
      |{{cfn-output:AsgCfnTemplate>AutoScalingGroupName}} |{{cfn-output:AutomationAssumeRoleTemplate>DigitoSimulateAzOutageInAsgAssumeRole}}|{{cfn-output:AsgCfnTemplate>SyntheticAlarm}}|{{cache:TestDurationInMinutes}}|
    Then SSM automation document "Digito-SimulateAzOutageInAsg_2020-07-23" execution in status "Success"
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation AZ outage on ASG instances in rollback mode
    Given the cached input parameters
      |InstanceType|TestDurationInMinutes|
      |    t2.small|                    5|
    And the cloud formation templates as integration test resources
      |CfnTemplatePath                                                                                          |ResourceType|InstanceType          |
      |resource_manager/cloud_formation_templates/AsgCfnTemplate.yml                                            |   ON_DEMAND|{{cache:InstanceType}}|
      |documents/compute/test/asg-availability_zone_outage/2020-07-23/Documents/AutomationAssumeRoleTemplate.yml| ASSUME_ROLE|                      |
    And published "Digito-SimulateAzOutageInAsg_2020-07-23" SSM document

    When SSM automation document "Digito-SimulateAzOutageInAsg_2020-07-23" executed
      |AutoScalingGroupName                               |AutomationAssumeRole                                                             |SyntheticAlarmName                          |TestDurationInMinutes          |
      |{{cfn-output:AsgCfnTemplate>AutoScalingGroupName}} |{{cfn-output:AutomationAssumeRoleTemplate>DigitoSimulateAzOutageInAsgAssumeRole}}|{{cfn-output:AsgCfnTemplate>SyntheticAlarm}}|{{cache:TestDurationInMinutes}}|

    And Wait for the SSM automation document "Digito-SimulateAzOutageInAsg_2020-07-23" execution is on step "TerminateInstances" in status "Success" for "180" seconds
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    Then terminate "Digito-SimulateAzOutageInAsg_2020-07-23" SSM automation document
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|

    Then Wait for the SSM automation document "Digito-SimulateAzOutageInAsg_2020-07-23" execution is on step "TriggerRollback" in status "Success" for "240" seconds
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|

    Then SSM automation document "Digito-SimulateAzOutageInAsg_2020-07-23" execution in status "Cancelled"
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|

    Then cache rollback execution id
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|

    Then SSM automation document "Digito-SimulateAzOutageInAsg_2020-07-23" execution in status "Success"
      |ExecutionId               |
      |{{cache:SsmExecutionId>2}}|