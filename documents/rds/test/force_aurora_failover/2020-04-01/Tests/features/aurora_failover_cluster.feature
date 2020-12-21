@rds @failover @integration
Feature: SSM automation document for Aurora cluster failover.
  Exercise RDS cluster failover using SSM automation document.

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document to failover RDS cluster with primary
    Given the cloud formation templates as integration test resources
      |CfnTemplatePath                                                                                |ResourceType|DBInstanceClass|AllocatedStorage|
      |resource_manager/cloud_formation_templates/RdsAuroraFailoverTestTemplate.yml                   |   ON_DEMAND|    db.t3.small|               1|
      |documents/rds/test/force_aurora_failover/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE|               |                |
    And cache DB cluster "dbReaderId" and "dbWriterId" "before" SSM automation execution
      |ClusterId                                             |
      |{{cfn-output:RdsAuroraFailoverTestTemplate>ClusterId}}|
    And SSM automation document "Digito-AuroraFailoverCluster" executed
      |ClusterId                                             |InstanceId                 |AutomationAssumeRole                                                             |SyntheticAlarmName                                             |
      |{{cfn-output:RdsAuroraFailoverTestTemplate>ClusterId}}|{{cache:before>dbReaderId}}|{{cfn-output:AutomationAssumeRoleTemplate>DigitoAuroraFailoverClusterAssumeRole}}|{{cfn-output:RdsAuroraFailoverTestTemplate>SyntheticAlarmName}}|

    When SSM automation document "Digito-AuroraFailoverCluster" execution in status "Success"
    And cache DB cluster "dbReaderId" and "dbWriterId" "after" SSM automation execution
      |ClusterId                                             |
      |{{cfn-output:RdsAuroraFailoverTestTemplate>ClusterId}}|

    Then assert DB cluster "dbReaderId" instance "before" failover became "dbWriterId" instance "after" failover
    And assert DB cluster "dbWriterId" instance "before" failover became "dbReaderId" instance "after" failover

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document to failover RDS cluster default
    Given the cloud formation templates as integration test resources
      |CfnTemplatePath                                                                                |ResourceType|DBInstanceClass|AllocatedStorage|
      |resource_manager/cloud_formation_templates/RdsAuroraFailoverTestTemplate.yml                   |   ON_DEMAND|    db.t3.small|               1|
      |documents/rds/test/force_aurora_failover/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE|               |                |
    And cache DB cluster "dbReaderId" and "dbWriterId" "before" SSM automation execution
      |ClusterId                                             |
      |{{cfn-output:RdsAuroraFailoverTestTemplate>ClusterId}}|
    And SSM automation document "Digito-AuroraFailoverCluster" executed
      |ClusterId                                             |AutomationAssumeRole                                             |SyntheticAlarmName                                             |
      |{{cfn-output:RdsAuroraFailoverTestTemplate>ClusterId}}|{{cfn-output:AutomationAssumeRoleTemplate>DigitoAuroraFailoverClusterAssumeRole}}|{{cfn-output:RdsAuroraFailoverTestTemplate>SyntheticAlarmName}}|

    When SSM automation document "Digito-AuroraFailoverCluster" execution in status "Success"
    And cache DB cluster "dbReaderId" and "dbWriterId" "after" SSM automation execution
     |ClusterId                                             |
     |{{cfn-output:RdsAuroraFailoverTestTemplate>ClusterId}}|

    Then assert DB cluster "dbReaderId" instance "before" failover became "dbWriterId" instance "after" failover
    And assert DB cluster "dbWriterId" instance "before" failover became "dbReaderId" instance "after" failover