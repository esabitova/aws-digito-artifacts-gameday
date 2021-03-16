@asg @asg_network_unavailable @integration
Feature: SSM automation document ASG Network Unavailable testing
  Exercise ASG Network Unavailable injection

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation network unavailable on EC2 instances in ASG
    Given the cached input parameters
      |InstanceType|PercentageOfInstances|DurationInMinutes|
      |    t2.small|                  100|                5|
    And the cloud formation templates as integration test resources
      |CfnTemplatePath                                                                                      |ResourceType|InstanceType          |
      |resource_manager/cloud_formation_templates/AsgCfnTemplate.yml                                        |   ON_DEMAND|{{cache:InstanceType}}|
      |documents/compute/test/asg-network_unavailable/2020-07-23/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE|                      |
    And published "Digito-SimulateNetworkUnavailableInAsg_2020-07-23" SSM document

    When SSM automation document "Digito-SimulateNetworkUnavailableInAsg_2020-07-23" executed
      |AutoScalingGroupName                              |AutomationAssumeRole                                                                       |MultipleUnhealthyHostsAlarmName                      |DurationInMinutes          |PercentageOfInstances          |
      |{{cfn-output:AsgCfnTemplate>AutoScalingGroupName}}|{{cfn-output:AutomationAssumeRoleTemplate>DigitoSimulateNetworkUnavailableInAsgAssumeRole}}|{{cfn-output:AsgCfnTemplate>UnHealthyHostCountAlarm}}|{{cache:DurationInMinutes}}|{{cache:PercentageOfInstances}}|

    Then SSM automation document "Digito-SimulateNetworkUnavailableInAsg_2020-07-23" execution in status "Success"
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|
