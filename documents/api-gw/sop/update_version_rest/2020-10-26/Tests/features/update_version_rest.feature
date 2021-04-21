@api-gw
Feature: SSM automation document to update REST API deployment

  Scenario: Accept given deployment id and applies it on the given stage with provided RestDeploymentId v2
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                | ResourceType |
      | resource_manager/cloud_formation_templates/RestApiGwTemplate.yml                               | ON_DEMAND    |
      | documents/api-gw/sop/update_version_rest/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestApiGwUpdateVersionRest_2020-10-26" SSM document
    And SSM automation document "Digito-RestApiGwUpdateVersionRest_2020-10-26" executed
      | RestApiGwId                                  | RestStageName                                       | RestDeploymentId                                         | AutomationAssumeRole                                                                      |
      | {{cfn-output:RestApiGwTemplate>RestApiGwId}} | {{cfn-output:RestApiGwTemplate>RestApiGwStageName}} | {{cfn-output:RestApiGwTemplate>RestApiGwDeploymentV2Id}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestApiGwUpdateVersionRestAssumeRoleArn}} |
    And SSM automation document "Digito-RestApiGwUpdateVersionRest_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

  Scenario: Accept given deployment id and applies it on the given stage with provided RestDeploymentId v1
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                | ResourceType |
      | resource_manager/cloud_formation_templates/RestApiGwTemplate.yml                               | ON_DEMAND    |
      | documents/api-gw/sop/update_version_rest/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestApiGwUpdateVersionRest_2020-10-26" SSM document
    And SSM automation document "Digito-RestApiGwUpdateVersionRest_2020-10-26" executed
      | RestApiGwId                                  | RestStageName                                       | RestDeploymentId                                       | AutomationAssumeRole                                                                      |
      | {{cfn-output:RestApiGwTemplate>RestApiGwId}} | {{cfn-output:RestApiGwTemplate>RestApiGwStageName}} | {{cfn-output:RestApiGwTemplate>RestApiGwDeploymentId}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestApiGwUpdateVersionRestAssumeRoleArn}} |
    And SSM automation document "Digito-RestApiGwUpdateVersionRest_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |

  Scenario: Accept given deployment id and applies it on the given stage with provided RestDeploymentId same as current
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                | ResourceType |
      | resource_manager/cloud_formation_templates/RestApiGwTemplate.yml                               | ON_DEMAND    |
      | documents/api-gw/sop/update_version_rest/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-RestApiGwUpdateVersionRest_2020-10-26" SSM document
    And SSM automation document "Digito-RestApiGwUpdateVersionRest_2020-10-26" executed
      | RestApiGwId                                  | RestStageName                                       | RestDeploymentId                                       | AutomationAssumeRole                                                                      |
      | {{cfn-output:RestApiGwTemplate>RestApiGwId}} | {{cfn-output:RestApiGwTemplate>RestApiGwStageName}} | {{cfn-output:RestApiGwTemplate>RestApiGwDeploymentId}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoRestApiGwUpdateVersionRestAssumeRoleArn}} |
    And SSM automation document "Digito-RestApiGwUpdateVersionRest_2020-10-26" execution in status "Failed"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |