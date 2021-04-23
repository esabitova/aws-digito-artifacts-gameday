@api-gw
Feature: SSM automation document to update REST API deployment

  Scenario: Run document with provided RestDeploymentId
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                | ResourceType |
      | resource_manager/cloud_formation_templates/RestApiGwTemplate.yml                               | ON_DEMAND    |
      | documents/api-gw/sop/update_version_rest/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestApiGwUpdateVersionRest_2020-10-26" SSM document
    And cache current deployment id as "CurrentDeploymentId" "before" SSM automation execution
      | RestApiGwId                                  | RestStageName                                       |
      | {{cfn-output:RestApiGwTemplate>RestApiGwId}} | {{cfn-output:RestApiGwTemplate>RestApiGwStageName}} |
    And create dummy deployment and cache id as "DeploymentIdToApply" "before" SSM automation execution
      | RestApiGwId                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwId}} |
    When SSM automation document "Digito-RestApiGwUpdateVersionRest_2020-10-26" executed
      | RestApiGwId                                  | RestStageName                                       | RestDeploymentId                     | AutomationAssumeRole                                                                      |
      | {{cfn-output:RestApiGwTemplate>RestApiGwId}} | {{cfn-output:RestApiGwTemplate>RestApiGwStageName}} | {{cache:before>DeploymentIdToApply}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestApiGwUpdateVersionRestAssumeRoleArn}} |
    Then SSM automation document "Digito-RestApiGwUpdateVersionRest_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache current deployment id as "CurrentDeploymentId" "after" SSM automation execution
      | RestApiGwId                                  | RestStageName                                       |
      | {{cfn-output:RestApiGwTemplate>RestApiGwId}} | {{cfn-output:RestApiGwTemplate>RestApiGwStageName}} |
    And update current deployment id and cache result as "RollbackResult" "after" SSM automation execution
      | RestApiGwId                                  | RestStageName                                       | RestDeploymentId                     |
      | {{cfn-output:RestApiGwTemplate>RestApiGwId}} | {{cfn-output:RestApiGwTemplate>RestApiGwStageName}} | {{cache:before>CurrentDeploymentId}} |
    And cache current deployment id as "RollbackDeploymentId" "after" SSM automation execution
      | RestApiGwId                                  | RestStageName                                       |
      | {{cfn-output:RestApiGwTemplate>RestApiGwId}} | {{cfn-output:RestApiGwTemplate>RestApiGwStageName}} |
    Then assert "DeploymentIdToApply" at "before" became equal to "CurrentDeploymentId" at "after"
    Then assert "CurrentDeploymentId" at "before" became equal to "RollbackDeploymentId" at "after"
    Then delete dummy deployment
      | RestApiGwId                                  | RestStageName                                       | RestDeploymentId                     |
      | {{cfn-output:RestApiGwTemplate>RestApiGwId}} | {{cfn-output:RestApiGwTemplate>RestApiGwStageName}} | {{cache:before>DeploymentIdToApply}} |


  Scenario: Run document with provided RestDeploymentId same as current deployment
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                | ResourceType |
      | resource_manager/cloud_formation_templates/RestApiGwTemplate.yml                               | ON_DEMAND    |
      | documents/api-gw/sop/update_version_rest/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestApiGwUpdateVersionRest_2020-10-26" SSM document
    And cache current deployment id as "CurrentDeploymentId" "before" SSM automation execution
      | RestApiGwId                                  | RestStageName                                       |
      | {{cfn-output:RestApiGwTemplate>RestApiGwId}} | {{cfn-output:RestApiGwTemplate>RestApiGwStageName}} |
    When SSM automation document "Digito-RestApiGwUpdateVersionRest_2020-10-26" executed
      | RestApiGwId                                  | RestStageName                                       | RestDeploymentId                     | AutomationAssumeRole                                                                      |
      | {{cfn-output:RestApiGwTemplate>RestApiGwId}} | {{cfn-output:RestApiGwTemplate>RestApiGwStageName}} | {{cache:before>CurrentDeploymentId}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestApiGwUpdateVersionRestAssumeRoleArn}} |
    Then SSM automation document "Digito-RestApiGwUpdateVersionRest_2020-10-26" execution in status "Failed"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

  Scenario: Run document without provided RestDeploymentId and without available deployments for update
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                | ResourceType |
      | resource_manager/cloud_formation_templates/RestApiGwTemplate.yml                               | ON_DEMAND    |
      | documents/api-gw/sop/update_version_rest/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestApiGwUpdateVersionRest_2020-10-26" SSM document
    When SSM automation document "Digito-RestApiGwUpdateVersionRest_2020-10-26" executed
      | RestApiGwId                                  | RestStageName                                       | AutomationAssumeRole                                                                      |
      | {{cfn-output:RestApiGwTemplate>RestApiGwId}} | {{cfn-output:RestApiGwTemplate>RestApiGwStageName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestApiGwUpdateVersionRestAssumeRoleArn}} |
    Then SSM automation document "Digito-RestApiGwUpdateVersionRest_2020-10-26" execution in status "Failed"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

  Scenario: Run document without provided RestDeploymentId and without previous deployments for update
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                | ResourceType |
      | resource_manager/cloud_formation_templates/RestApiGwTemplate.yml                               | ON_DEMAND    |
      | documents/api-gw/sop/update_version_rest/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestApiGwUpdateVersionRest_2020-10-26" SSM document
    And create dummy deployment and cache id as "DummyDeploymentId" "before" SSM automation execution
      | RestApiGwId                                  |
      | {{cfn-output:RestApiGwTemplate>RestApiGwId}} |
    When SSM automation document "Digito-RestApiGwUpdateVersionRest_2020-10-26" executed
      | RestApiGwId                                  | RestStageName                                       | AutomationAssumeRole                                                                      |
      | {{cfn-output:RestApiGwTemplate>RestApiGwId}} | {{cfn-output:RestApiGwTemplate>RestApiGwStageName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestApiGwUpdateVersionRestAssumeRoleArn}} |
    Then SSM automation document "Digito-RestApiGwUpdateVersionRest_2020-10-26" execution in status "Failed"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    Then delete dummy deployment
      | RestApiGwId                                  | RestStageName                                       | RestDeploymentId                   |
      | {{cfn-output:RestApiGwTemplate>RestApiGwId}} | {{cfn-output:RestApiGwTemplate>RestApiGwStageName}} | {{cache:before>DummyDeploymentId}} |
