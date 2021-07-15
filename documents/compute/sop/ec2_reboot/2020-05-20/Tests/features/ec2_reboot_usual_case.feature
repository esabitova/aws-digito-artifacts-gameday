@ec2 @integration
Feature: SSM automation document Digito-Ec2Reboot_2020-05-20

  Scenario: Execute SSM automation document Digito-Ec2Reboot_2020-05-20
    Given the cached input parameters
      | AlarmGreaterThanOrEqualToThreshold | InstanceType |
      | 99                                 | t2.small     |

    And the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                        | ResourceType | InstanceType           | AlarmGreaterThanOrEqualToThreshold           |
      | resource_manager/cloud_formation_templates/EC2WithCWAgentCfnTemplate.yml               | ON_DEMAND    | {{cache:InstanceType}} | {{cache:AlarmGreaterThanOrEqualToThreshold}} |
      | documents/compute/sop/ec2_reboot/2020-05-20/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                        |                                              |
    And published "Digito-Ec2Reboot_2020-05-20" SSM document

    When SSM automation document "Digito-Ec2Reboot_2020-05-20" executed
      | EC2InstanceIdentifier                               | AutomationAssumeRole                                                         |
      | {{cfn-output:EC2WithCWAgentCfnTemplate>InstanceId}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoComputeEc2RebootAssumeRole}} |

    Then SSM automation document "Digito-Ec2Reboot_2020-05-20" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
