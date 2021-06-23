@rds @rds_backtrack @integration
Feature: SSM automation document for Aurora backtrack sop.
  Exercise SSM automation document for aurora backtrack.

  Scenario: Create AWS resources using CloudFormation template and execute SSM automation document to backtrack
    Given the cloud formation templates as integration test resources
      |CfnTemplatePath                                                                  |ResourceType|DBInstanceClass|
      |resource_manager/cloud_formation_templates/RdsAuroraWithBacktrackTemplate.yml    |   ON_DEMAND|    db.t3.small|
      |documents/rds/sop/backtrack/2020-04-01/Documents/AutomationAssumeRoleTemplate.yml| ASSUME_ROLE|               |
    And published "Digito-RdsBacktrack_2020-04-01" SSM document

    And cache backtrack time "backtrack_time"

    When SSM automation document "Digito-RdsBacktrack_2020-04-01" executed
      |DbClusterIdentifier                                    |AutomationAssumeRole                                                    |BacktrackTo             |
      |{{cfn-output:RdsAuroraWithBacktrackTemplate>ClusterId}}|{{cfn-output:AutomationAssumeRoleTemplate>DigitoRdsBacktrackAssumeRole}}|{{cache:backtrack_time}}|
    And SSM automation document "Digito-RdsBacktrack_2020-04-01" execution in status "Success"
      |ExecutionId               |
      |{{cache:SsmExecutionId>1}}|
