@compute @integration @ec2_scale_up
Feature: SSM automation document Digito-Ec2ScaleUp_2020-05-20

  Scenario: Execute SSM automation document Digito-Ec2ScaleUp_2020-05-20 and without instance type override
    Given the cached input parameters
      | AlarmGreaterThanOrEqualToThreshold | InstanceType |
      | 99                                 | t2.small     |

    And the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                          | ResourceType | InstanceType           | AlarmGreaterThanOrEqualToThreshold           |
      | resource_manager/cloud_formation_templates/EC2WithCWAgentCfnTemplate.yml                 | ON_DEMAND    | {{cache:InstanceType}} | {{cache:AlarmGreaterThanOrEqualToThreshold}} |
      | documents/compute/sop/ec2_scale_up/2020-05-20/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                        |                                              |

    And published "Digito-Ec2ScaleUp_2020-05-20" SSM document

    And SSM automation document "Digito-Ec2ScaleUp_2020-05-20" executed
      | EC2InstanceIdentifier                               | AutomationAssumeRole                                                          |
      | {{cfn-output:EC2WithCWAgentCfnTemplate>InstanceId}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoComputeEc2ScaleUpAssumeRole}} |

    When SSM automation document "Digito-Ec2ScaleUp_2020-05-20" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    And cache execution output value of "CalculateTargetType.TargetInstanceType" as "TargetInstanceType" after SSM automation execution
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    Then assert "TargetInstanceType" at "after" became equal to "t2.medium"

  Scenario: Execute SSM automation document Digito-Ec2ScaleUp_2020-05-20 and with instance type override
    Given the cached input parameters
      | AlarmGreaterThanOrEqualToThreshold | InstanceType |
      | 99                                 | t2.small     |

    And the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                          | ResourceType | InstanceType           | AlarmGreaterThanOrEqualToThreshold           |
      | resource_manager/cloud_formation_templates/EC2WithCWAgentCfnTemplate.yml                 | ON_DEMAND    | {{cache:InstanceType}} | {{cache:AlarmGreaterThanOrEqualToThreshold}} |
      | documents/compute/sop/ec2_scale_up/2020-05-20/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |                        |                                              |

    And published "Digito-Ec2ScaleUp_2020-05-20" SSM document

    And SSM automation document "Digito-Ec2ScaleUp_2020-05-20" executed
      | EC2InstanceIdentifier                               | EC2InstanceTargetInstanceType | AutomationAssumeRole                                                          |
      | {{cfn-output:EC2WithCWAgentCfnTemplate>InstanceId}} | t2.xlarge                     | {{cfn-output:AutomationAssumeRoleTemplate>DigitoComputeEc2ScaleUpAssumeRole}} |

    When SSM automation document "Digito-Ec2ScaleUp_2020-05-20" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    And cache execution output value of "CalculateTargetType.TargetInstanceType" as "TargetInstanceType" after SSM automation execution
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

    Then assert "TargetInstanceType" at "after" became equal to "t2.xlarge"
