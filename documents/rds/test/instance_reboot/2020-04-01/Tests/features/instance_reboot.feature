@rds @instance_reboot @integration
Feature: SSM automation document for RDS instance failover.
  Exercise RDS instance reboot using SSM automation document.

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document to reboot RDS instance
    Given the cloud formation templates as integration test resources
      |CfnTemplatePath                                                                         |ResourceType|DBInstanceClass|AllocatedStorage|
      |resource_manager/cloud_formation_templates/RdsCfnTemplate.yml                           |   ON_DEMAND|    db.t3.small|              20|
      |documents/rds/test/instance_reboot/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml| ASSUME_ROLE|               |                |
    And published "Digito-RebootRdsInstance_2020-04-01" SSM document

    When SSM automation document "Digito-RebootRdsInstance_2020-04-01" executed
      |DbInstanceId                            |AutomationAssumeRole                                                         |SyntheticAlarmName                              |
      |{{cfn-output:RdsCfnTemplate>InstanceId}}|{{cfn-output:AutomationAssumeRoleTemplate>DigitoRebootRdsInstanceAssumeRole}}|{{cfn-output:RdsCfnTemplate>SyntheticAlarmName}}|
    And SSM automation document "Digito-RebootRdsInstance_2020-04-01" execution in status "Success"
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|