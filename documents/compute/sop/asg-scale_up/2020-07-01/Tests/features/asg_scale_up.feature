@asg @integration @asg_scale_up
Feature: SSM automation document ASG scale up testing
  Exercise ASG scale up sop

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation scale up on ASG with LaunchConfig
    Given the cached input parameters
      |InstanceType|
      |    t2.small|
    And the cloud formation templates as integration test resources
      |CfnTemplatePath                                                                          | ResourceType | InstanceType          |
      |resource_manager/cloud_formation_templates/AsgCfnTemplate.yml                            | ON_DEMAND    | {{cache:InstanceType}}|
      |documents/compute/sop/asg-scale_up/2020-07-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                       |
    And published "Digito-ASG-ScaleUp_2020-04-01" SSM document

    When SSM automation document "Digito-ASG-ScaleUp_2020-04-01" executed
      |AutoScalingGroupName                               |AutomationAssumeRole                                                  |
      |{{cfn-output:AsgCfnTemplate>AutoScalingGroupName}} |{{cfn-output:AutomationAssumeRoleTemplate>DigitoAsgScaleUpAssumeRole}}|
    Then SSM automation document "Digito-ASG-ScaleUp_2020-04-01" execution in status "Success"
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation scale up on ASG with LaunchTemplate
    Given the cached input parameters
      |InstanceType|
      |    t2.small|
    And the cloud formation templates as integration test resources
      |CfnTemplatePath                                                                          | ResourceType | InstanceType          |
      |resource_manager/cloud_formation_templates/AsgLaunchTemplateCfnTemplate.yml              | ON_DEMAND    | {{cache:InstanceType}}|
      |documents/compute/sop/asg-scale_up/2020-07-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                       |
    And published "Digito-ASG-ScaleUp_2020-04-01" SSM document

    When SSM automation document "Digito-ASG-ScaleUp_2020-04-01" executed
      |AutoScalingGroupName                               |AutomationAssumeRole                                                  |
      |{{cfn-output:AsgLaunchTemplateCfnTemplate>AutoScalingGroupName}} |{{cfn-output:AutomationAssumeRoleTemplate>DigitoAsgScaleUpAssumeRole}}|
    Then SSM automation document "Digito-ASG-ScaleUp_2020-04-01" execution in status "Success"
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|