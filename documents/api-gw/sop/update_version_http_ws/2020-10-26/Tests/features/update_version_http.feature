@api-gw
Feature: SSM automation document to update api gateway deployment version

  Scenario: Run document for HTTP Api with a specified deployment Id
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                   | ResourceType |
      | resource_manager/cloud_formation_templates/HTTPWSApiGwTemplate.yml                                | ON_DEMAND    |
      | documents/api-gw/sop/update_version_http_ws/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-UpdateHttpWsApiGwVersionSOP_2020-10-26" SSM document
    And cache current ws or http deployment id as "DeploymentId" "before" SSM automation execution
      | HttpWsApiGwId                                  | HttpWsStageName                                  |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageName}} |
    And create dummy ws or http deployment and cache id as "DeploymentIdToApply" "before" SSM automation execution
      | HttpWsApiGwId                                  | BackupDeploymentId            | HttpWsStageName                                  |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cache:before>DeploymentId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageName}} |

    When SSM automation document "Digito-UpdateHttpWsApiGwVersionSOP_2020-10-26" executed
      | HttpWsApiGwId                                  | HttpWsStageName                                  | HttpWsDeploymentId                   | AutomationAssumeRole                                                                    |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageName}} | {{cache:before>DeploymentIdToApply}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoUpdateHttpWsApiGwVersionSOPAssumeRole}} |

    Then SSM automation document "Digito-UpdateHttpWsApiGwVersionSOP_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache current ws or http deployment id as "DeploymentId" "after" SSM automation execution
      | HttpWsApiGwId                                  | HttpWsStageName                                  |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageName}} |
    And assert "DeploymentIdToApply" at "before" became equal to "DeploymentId" at "after"


  Scenario: Run document for WS Api for stage with AutoDeploy and expect failure as AutoDeploy is not supported
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                   | ResourceType |
      | resource_manager/cloud_formation_templates/HTTPWSApiGwTemplate.yml                                | ON_DEMAND    |
      | documents/api-gw/sop/update_version_http_ws/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-UpdateHttpWsApiGwVersionSOP_2020-10-26" SSM document
    And cache current ws or http deployment id as "DeploymentId" "before" SSM automation execution
      | HttpWsApiGwId                                  | HttpWsStageName                                            |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageNameAutoDeploy}} |
    And create dummy ws or http deployment and cache id as "DeploymentIdToApply" "before" SSM automation execution
      | HttpWsApiGwId                                  | BackupDeploymentId            | HttpWsStageName                                            |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cache:before>DeploymentId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageNameAutoDeploy}} |
    When SSM automation document "Digito-UpdateHttpWsApiGwVersionSOP_2020-10-26" executed
      | HttpWsApiGwId                                  | HttpWsStageName                                            | HttpWsDeploymentId                   | AutomationAssumeRole                                                                    |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageNameAutoDeploy}} | {{cache:before>DeploymentIdToApply}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoUpdateHttpWsApiGwVersionSOPAssumeRole}} |
    Then SSM automation document "Digito-UpdateHttpWsApiGwVersionSOP_2020-10-26" execution in status "Failed"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |


  Scenario: Run document for HTTP Api with provided deployment same as current
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                   | ResourceType |
      | resource_manager/cloud_formation_templates/HTTPWSApiGwTemplate.yml                                | ON_DEMAND    |
      | documents/api-gw/sop/update_version_http_ws/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-UpdateHttpWsApiGwVersionSOP_2020-10-26" SSM document
    And cache current ws or http deployment id as "DeploymentId" "before" SSM automation execution
      | HttpWsApiGwId                                  | HttpWsStageName                                  |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageName}} |
    When SSM automation document "Digito-UpdateHttpWsApiGwVersionSOP_2020-10-26" executed
      | HttpWsApiGwId                                  | HttpWsStageName                                  | HttpWsDeploymentId            | AutomationAssumeRole                                                                    |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageName}} | {{cache:before>DeploymentId}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoUpdateHttpWsApiGwVersionSOPAssumeRole}} |
    Then SSM automation document "Digito-UpdateHttpWsApiGwVersionSOP_2020-10-26" execution in status "Failed"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |


  Scenario: Run document for HTTP Api without provided deployment Id
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                   | ResourceType |
      | resource_manager/cloud_formation_templates/HTTPWSApiGwTemplate.yml                                | ON_DEMAND    |
      | documents/api-gw/sop/update_version_http_ws/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-UpdateHttpWsApiGwVersionSOP_2020-10-26" SSM document
    And cache current ws or http deployment id as "DeploymentId" "before" SSM automation execution
      | HttpWsApiGwId                                  | HttpWsStageName                                  |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageName}} |
    And create "10" dummy ws or http deployments with interval "3" seconds and cache ids as "DummyDeployments" "before" SSM automation execution
      | HttpWsApiGwId                                  | BackupDeploymentId            | HttpWsStageName                                  |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cache:before>DeploymentId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageName}} |
    And set dummy ws or http deployment number "5" as current and cache previous deployment as "ExpectedDeploymentId" "before" SSM automation execution
      | HttpWsApiGwId                                  | HttpWsStageName                                  | DummyDeployments                  |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageName}} | {{cache:before>DummyDeployments}} |

    When SSM automation document "Digito-UpdateHttpWsApiGwVersionSOP_2020-10-26" executed
      | HttpWsApiGwId                                  | HttpWsStageName                                  | AutomationAssumeRole                                                                    |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoUpdateHttpWsApiGwVersionSOPAssumeRole}} |

    Then SSM automation document "Digito-UpdateHttpWsApiGwVersionSOP_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache current ws or http deployment id as "DeploymentId" "after" SSM automation execution
      | HttpWsApiGwId                                  | HttpWsStageName                                  |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageName}} |
    And assert "ExpectedDeploymentId" at "before" became equal to "DeploymentId" at "after"


  Scenario: Run document for HTTP Api without provided deployment Id and without available deployments
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                   | ResourceType |
      | resource_manager/cloud_formation_templates/HTTPWSApiGwTemplate.yml                                | ON_DEMAND    |
      | documents/api-gw/sop/update_version_http_ws/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-UpdateHttpWsApiGwVersionSOP_2020-10-26" SSM document
    When SSM automation document "Digito-UpdateHttpWsApiGwVersionSOP_2020-10-26" executed
      | HttpWsApiGwId                                  | HttpWsStageName                                  | AutomationAssumeRole                                                                    |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoUpdateHttpWsApiGwVersionSOPAssumeRole}} |

    Then SSM automation document "Digito-UpdateHttpWsApiGwVersionSOP_2020-10-26" execution in status "Failed"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |


  Scenario: Run document for HTTP Api without provided deployment Id and without available previous deployments
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                   | ResourceType |
      | resource_manager/cloud_formation_templates/HTTPWSApiGwTemplate.yml                                | ON_DEMAND    |
      | documents/api-gw/sop/update_version_http_ws/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-UpdateHttpWsApiGwVersionSOP_2020-10-26" SSM document
    And cache current ws or http deployment id as "DeploymentId" "before" SSM automation execution
      | HttpWsApiGwId                                  | HttpWsStageName                                  |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageName}} |
    And create dummy ws or http deployment and cache id as "DeploymentIdToApply" "before" SSM automation execution
      | HttpWsApiGwId                                  | BackupDeploymentId            | HttpWsStageName                                  |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cache:before>DeploymentId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageName}} |

    When SSM automation document "Digito-UpdateHttpWsApiGwVersionSOP_2020-10-26" executed
      | HttpWsApiGwId                                  | HttpWsStageName                                  | AutomationAssumeRole                                                                    |
      | {{cfn-output:HTTPWSApiGwTemplate>HttpApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>HttpStageName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoUpdateHttpWsApiGwVersionSOPAssumeRole}} |

    Then SSM automation document "Digito-UpdateHttpWsApiGwVersionSOP_2020-10-26" execution in status "Failed"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |