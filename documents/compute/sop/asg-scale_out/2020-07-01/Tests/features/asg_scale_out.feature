@asg @integration @asg_scale_out
Feature: SSM automation document ASG scale out testing
  Exercise ASG scale out sop

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation scale out on ASG instances
    Given the cached input parameters
      |InstanceType|
      |    t2.small|
    And the cloud formation templates as integration test resources
      |CfnTemplatePath                                                                           |ResourceType|InstanceType          |
      |resource_manager/cloud_formation_templates/AsgCfnTemplate.yml                             |   ON_DEMAND|{{cache:InstanceType}}|
      |documents/compute/sop/asg-scale_out/2020-07-01/Documents/AutomationAssumeRoleTemplate.yml| ASSUME_ROLE|                      |
    And published "Digito-ASG-ScaleOut_2020-07-01" SSM document

    When SSM automation document "Digito-ASG-ScaleOut_2020-07-01" executed
      |AutoScalingGroupName                               |AutomationAssumeRole                                                   |
      |{{cfn-output:AsgCfnTemplate>AutoScalingGroupName}} |{{cfn-output:AutomationAssumeRoleTemplate>DigitoAsgScaleOutAssumeRole}}|
    Then SSM automation document "Digito-ASG-ScaleOut_2020-07-01" execution in status "Success"
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|
