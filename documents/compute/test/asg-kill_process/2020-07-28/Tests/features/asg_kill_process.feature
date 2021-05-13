@asg @integration @asg_kill_process
Feature: SSM automation document ASG kill process document testing

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation to kill process on asg
    Given the cached input parameters
      |InstanceType|ProcessName|ExpectedRecoveryTimeInMinutes|PercentageOfInstances|
      |    t2.small|      httpd|                           10|                  100|
    And the cloud formation templates as integration test resources
      |CfnTemplatePath                                                                              |ResourceType|InstanceType          |
      |resource_manager/cloud_formation_templates/AsgCfnTemplate.yml                                |   ON_DEMAND|{{cache:InstanceType}}|
      |documents/compute/test/asg-kill_process/2020-07-28/Documents/AutomationAssumeRoleTemplate.yml| ASSUME_ROLE|                      |
      |documents/compute/test/asg-node_replace/2020-07-23/Documents/AutomationAssumeRoleTemplate.yml| ASSUME_ROLE|                      |

    And published "Digito-KillProcessAsg_2020-07-28" SSM document

    When SSM automation document "Digito-KillProcessAsg_2020-07-28" executed
      |AutoScalingGroupName                              |          ExpectedRecoveryTimeInMinutes|AutomationAssumeRole                                                      |PercentageOfInstances          |MultipleUnhealthyHostsAlarmName                      |ProcessName          |
      |{{cfn-output:AsgCfnTemplate>AutoScalingGroupName}}|{{cache:ExpectedRecoveryTimeInMinutes}}|{{cfn-output:AutomationAssumeRoleTemplate>DigitoKillProcessAsgAssumeRole}}|{{cache:PercentageOfInstances}}|{{cfn-output:AsgCfnTemplate>UnHealthyHostCountAlarm}}|{{cache:ProcessName}}|

    Then SSM automation document "Digito-KillProcessAsg_2020-07-28" execution in status "Success"
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation to kill process on asg, process does not exist
    Given the cached input parameters
      |InstanceType|ProcessName         |
      |    t2.small|non_existing_process|
    And the cloud formation templates as integration test resources
      |CfnTemplatePath                                                                              |ResourceType|InstanceType          |
      |resource_manager/cloud_formation_templates/AsgCfnTemplate.yml                                |   ON_DEMAND|{{cache:InstanceType}}|
      |documents/compute/test/asg-kill_process/2020-07-28/Documents/AutomationAssumeRoleTemplate.yml| ASSUME_ROLE|                      |

    And published "Digito-KillProcessAsg_2020-07-28" SSM document

    When SSM automation document "Digito-KillProcessAsg_2020-07-28" executed
      |AutoScalingGroupName                              |AutomationAssumeRole                                                      |MultipleUnhealthyHostsAlarmName                      |ProcessName          |
      |{{cfn-output:AsgCfnTemplate>AutoScalingGroupName}}|{{cfn-output:AutomationAssumeRoleTemplate>DigitoKillProcessAsgAssumeRole}}|{{cfn-output:AsgCfnTemplate>UnHealthyHostCountAlarm}}|{{cache:ProcessName}}|

    Then SSM automation document "Digito-KillProcessAsg_2020-07-28" execution in status "Failed"
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|