@asg @integration @kill_process
Feature: SSM automation document ASG kill process document testing

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation to kill process on asg
    Given the cached input parameters
      |InstanceType|ProcessName|ExpectedRecoveryTimeInSeconds|
      |    t2.small|      httpd|                           30|
    And the cloud formation templates as integration test resources
      |CfnTemplatePath                                                                              |ResourceType|InstanceType          |
      |resource_manager/cloud_formation_templates/AsgCfnTemplate.yml                                |   ON_DEMAND|{{cache:InstanceType}}|
      |documents/compute/test/asg-kill_process/2020-07-28/Documents/AutomationAssumeRoleTemplate.yml| ASSUME_ROLE|                      |
      |documents/compute/test/asg-node_replace/2020-07-23/Documents/AutomationAssumeRoleTemplate.yml| ASSUME_ROLE|                      |

    And published "Digito-RefreshAsgInstances_2020-07-23" SSM document

    And SSM automation document "Digito-RefreshAsgInstances_2020-07-23" executed
      |AutoScalingGroupName                              |AutomationAssumeRole                                                           |PercentageOfInstances|SyntheticAlarmName                          |
      |{{cfn-output:AsgCfnTemplate>AutoScalingGroupName}}|{{cfn-output:AutomationAssumeRoleTemplate>DigitoRefreshAsgInstancesAssumeRole}}|                  100|{{cfn-output:AsgCfnTemplate>SyntheticAlarm}}|
    And SSM automation document "Digito-RefreshAsgInstances_2020-07-23" execution in status "Success"
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|

    And published "Digito-KillProcessAsg_2020-07-28" SSM document

    When SSM automation document "Digito-KillProcessAsg_2020-07-28" executed
      |AutoScalingGroupName                              |          ExpectedRecoveryTimeInSeconds|AutomationAssumeRole                                                      |SyntheticAlarmName                          |ProcessName          |
      |{{cfn-output:AsgCfnTemplate>AutoScalingGroupName}}|{{cache:ExpectedRecoveryTimeInSeconds}}|{{cfn-output:AutomationAssumeRoleTemplate>DigitoKillProcessAsgAssumeRole}}|{{cfn-output:AsgCfnTemplate>SyntheticAlarm}}|{{cache:ProcessName}}|

    Then SSM automation document "Digito-KillProcessAsg_2020-07-28" execution in status "Success"
      |ExecutionId               |
      |{{cache:SsmExecutionId>2}}|

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
      |AutoScalingGroupName                              |AutomationAssumeRole                                                      |SyntheticAlarmName                          |ProcessName          |
      |{{cfn-output:AsgCfnTemplate>AutoScalingGroupName}}|{{cfn-output:AutomationAssumeRoleTemplate>DigitoKillProcessAsgAssumeRole}}|{{cfn-output:AsgCfnTemplate>SyntheticAlarm}}|{{cache:ProcessName}}|

    Then SSM automation document "Digito-KillProcessAsg_2020-07-28" execution in status "Failed"
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|