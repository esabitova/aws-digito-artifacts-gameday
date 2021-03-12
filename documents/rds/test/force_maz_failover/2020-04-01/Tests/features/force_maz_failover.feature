@rds @force_maz_failover @integration
Feature: SSM automation document for RDS instance failover.
  Exercise RDS instance failover using SSM automation document.

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document to failover RDS instance
    Given the cloud formation templates as integration test resources
      |CfnTemplatePath                                                                                |ResourceType|DBInstanceClass|AllocatedStorage|
      |resource_manager/cloud_formation_templates/RdsCfnTemplate.yml                                  |   ON_DEMAND|    db.t3.small|              20|
      |documents/rds/test/force_maz_failover/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml    | ASSUME_ROLE|               |                |
    And published "Digito-FailoverRdsInstance_2020-04-01" SSM document

    When SSM automation document "Digito-FailoverRdsInstance_2020-04-01" executed
      |DbInstanceId                            |AutomationAssumeRole                                                           |SyntheticAlarmName                              |
      |{{cfn-output:RdsCfnTemplate>InstanceId}}|{{cfn-output:AutomationAssumeRoleTemplate>DigitoFailoverRdsInstanceAssumeRole}}|{{cfn-output:RdsCfnTemplate>SyntheticAlarmName}}|
    And SSM automation document "Digito-FailoverRdsInstance_2020-04-01" execution in status "Success"
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|