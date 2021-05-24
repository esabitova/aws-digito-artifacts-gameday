@api-gw
Feature: SSM automation document to update api gateway deployment version

  Scenario: Run document for WS Api with a specified deployment Id
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                   | ResourceType |
      | resource_manager/cloud_formation_templates/HTTPWSApiGwTemplate.yml                                | ON_DEMAND    |
      | documents/api-gw/sop/update_version_http_ws/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-UpdateVersionHttpWs_2020-10-26" SSM document
    And cache current ws or http deployment id as "DeploymentId" "before" SSM automation execution
      | HttpWsApiGwId                                | HttpWsStageName                                |
      | {{cfn-output:HTTPWSApiGwTemplate>WsApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>WsStageName}} |
    And create dummy ws or http deployment and cache id as "DeploymentIdToApply" "before" SSM automation execution
      | HttpWsApiGwId                                | BackupDeploymentId            | HttpWsStageName                                |
      | {{cfn-output:HTTPWSApiGwTemplate>WsApiGwId}} | {{cache:before>DeploymentId}} | {{cfn-output:HTTPWSApiGwTemplate>WsStageName}} |

    When SSM automation document "Digito-UpdateVersionHttpWs_2020-10-26" executed
      | HttpWsApiGwId                                | HttpWsStageName                                | HttpWsDeploymentId                   | AutomationAssumeRole                                                                 |
      | {{cfn-output:HTTPWSApiGwTemplate>WsApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>WsStageName}} | {{cache:before>DeploymentIdToApply}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoApiGwUpdateVersionHttpWsAssumeRole}} |

    Then SSM automation document "Digito-UpdateVersionHttpWs_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache current ws or http deployment id as "DeploymentId" "after" SSM automation execution
      | HttpWsApiGwId                                | HttpWsStageName                                |
      | {{cfn-output:HTTPWSApiGwTemplate>WsApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>WsStageName}} |
    And assert "DeploymentIdToApply" at "before" became equal to "DeploymentId" at "after"


  Scenario: Run document for WS Api for stage with AutoDeploy and expect failure as AutoDeploy is not supported
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                   | ResourceType |
      | resource_manager/cloud_formation_templates/HTTPWSApiGwTemplate.yml                                | ON_DEMAND    |
      | documents/api-gw/sop/update_version_http_ws/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-UpdateVersionHttpWs_2020-10-26" SSM document
    And cache current ws or http deployment id as "DeploymentId" "before" SSM automation execution
      | HttpWsApiGwId                                | HttpWsStageName                                          |
      | {{cfn-output:HTTPWSApiGwTemplate>WsApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>WsStageNameAutoDeploy}} |
    And create dummy ws or http deployment and cache id as "DeploymentIdToApply" "before" SSM automation execution
      | HttpWsApiGwId                                | BackupDeploymentId            | HttpWsStageName                                          |
      | {{cfn-output:HTTPWSApiGwTemplate>WsApiGwId}} | {{cache:before>DeploymentId}} | {{cfn-output:HTTPWSApiGwTemplate>WsStageNameAutoDeploy}} |
    When SSM automation document "Digito-UpdateVersionHttpWs_2020-10-26" executed
      | HttpWsApiGwId                                | HttpWsStageName                                          | HttpWsDeploymentId                   | AutomationAssumeRole                                                                 |
      | {{cfn-output:HTTPWSApiGwTemplate>WsApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>WsStageNameAutoDeploy}} | {{cache:before>DeploymentIdToApply}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoApiGwUpdateVersionHttpWsAssumeRole}} |
    Then SSM automation document "Digito-UpdateVersionHttpWs_2020-10-26" execution in status "Failed"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |


  Scenario: Run document for WS Api with provided deployment same as current
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                   | ResourceType |
      | resource_manager/cloud_formation_templates/HTTPWSApiGwTemplate.yml                                | ON_DEMAND    |
      | documents/api-gw/sop/update_version_http_ws/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-UpdateVersionHttpWs_2020-10-26" SSM document
    And cache current ws or http deployment id as "DeploymentId" "before" SSM automation execution
      | HttpWsApiGwId                                | HttpWsStageName                                |
      | {{cfn-output:HTTPWSApiGwTemplate>WsApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>WsStageName}} |
    When SSM automation document "Digito-UpdateVersionHttpWs_2020-10-26" executed
      | HttpWsApiGwId                                | HttpWsStageName                                | HttpWsDeploymentId            | AutomationAssumeRole                                                                 |
      | {{cfn-output:HTTPWSApiGwTemplate>WsApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>WsStageName}} | {{cache:before>DeploymentId}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoApiGwUpdateVersionHttpWsAssumeRole}} |
    Then SSM automation document "Digito-UpdateVersionHttpWs_2020-10-26" execution in status "Failed"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |


  Scenario: Run document for WS Api without provided deployment Id
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                   | ResourceType |
      | resource_manager/cloud_formation_templates/HTTPWSApiGwTemplate.yml                                | ON_DEMAND    |
      | documents/api-gw/sop/update_version_http_ws/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-UpdateVersionHttpWs_2020-10-26" SSM document
    And cache current ws or http deployment id as "DeploymentId" "before" SSM automation execution
      | HttpWsApiGwId                                | HttpWsStageName                                |
      | {{cfn-output:HTTPWSApiGwTemplate>WsApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>WsStageName}} |
    And create "10" dummy ws or http deployments with interval "3" seconds and cache ids as "DummyDeployments" "before" SSM automation execution
      | HttpWsApiGwId                                | BackupDeploymentId            | HttpWsStageName                                |
      | {{cfn-output:HTTPWSApiGwTemplate>WsApiGwId}} | {{cache:before>DeploymentId}} | {{cfn-output:HTTPWSApiGwTemplate>WsStageName}} |
    And set dummy ws or http deployment number "5" as current and cache previous deployment as "ExpectedDeploymentId" "before" SSM automation execution
      | HttpWsApiGwId                                | HttpWsStageName                                | DummyDeployments                  |
      | {{cfn-output:HTTPWSApiGwTemplate>WsApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>WsStageName}} | {{cache:before>DummyDeployments}} |

    When SSM automation document "Digito-UpdateVersionHttpWs_2020-10-26" executed
      | HttpWsApiGwId                                | HttpWsStageName                                | AutomationAssumeRole                                                                 |
      | {{cfn-output:HTTPWSApiGwTemplate>WsApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>WsStageName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoApiGwUpdateVersionHttpWsAssumeRole}} |

    Then SSM automation document "Digito-UpdateVersionHttpWs_2020-10-26" execution in status "Success"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |
    And cache current ws or http deployment id as "DeploymentId" "after" SSM automation execution
      | HttpWsApiGwId                                | HttpWsStageName                                |
      | {{cfn-output:HTTPWSApiGwTemplate>WsApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>WsStageName}} |
    And assert "ExpectedDeploymentId" at "before" became equal to "DeploymentId" at "after"


  Scenario: Run document for WS Api without provided deployment Id and without available deployments
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                   | ResourceType |
      | resource_manager/cloud_formation_templates/HTTPWSApiGwTemplate.yml                                | ON_DEMAND    |
      | documents/api-gw/sop/update_version_http_ws/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-UpdateVersionHttpWs_2020-10-26" SSM document
    When SSM automation document "Digito-UpdateVersionHttpWs_2020-10-26" executed
      | HttpWsApiGwId                                | HttpWsStageName                                | AutomationAssumeRole                                                                 |
      | {{cfn-output:HTTPWSApiGwTemplate>WsApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>WsStageName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoApiGwUpdateVersionHttpWsAssumeRole}} |

    Then SSM automation document "Digito-UpdateVersionHttpWs_2020-10-26" execution in status "Failed"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |


  Scenario: Run document for WS Api without provided deployment Id and without available previous deployments
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                                   | ResourceType |
      | resource_manager/cloud_formation_templates/HTTPWSApiGwTemplate.yml                                | ON_DEMAND    |
      | documents/api-gw/sop/update_version_http_ws/2020-10-26/Documents/AutomationAssumeRoleTemplate.yml | ASSUME_ROLE  |
    And published "Digito-UpdateVersionHttpWs_2020-10-26" SSM document
    And cache current ws or http deployment id as "DeploymentId" "before" SSM automation execution
      | HttpWsApiGwId                                | HttpWsStageName                                |
      | {{cfn-output:HTTPWSApiGwTemplate>WsApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>WsStageName}} |
    And create dummy ws or http deployment and cache id as "DeploymentIdToApply" "before" SSM automation execution
      | HttpWsApiGwId                                | BackupDeploymentId            | HttpWsStageName                                |
      | {{cfn-output:HTTPWSApiGwTemplate>WsApiGwId}} | {{cache:before>DeploymentId}} | {{cfn-output:HTTPWSApiGwTemplate>WsStageName}} |

    When SSM automation document "Digito-UpdateVersionHttpWs_2020-10-26" executed
      | HttpWsApiGwId                                | HttpWsStageName                                | AutomationAssumeRole                                                                 |
      | {{cfn-output:HTTPWSApiGwTemplate>WsApiGwId}} | {{cfn-output:HTTPWSApiGwTemplate>WsStageName}} | {{cfn-output:AutomationAssumeRoleTemplate>DigitoApiGwUpdateVersionHttpWsAssumeRole}} |

    Then SSM automation document "Digito-UpdateVersionHttpWs_2020-10-26" execution in status "Failed"
      | ExecutionId                |
      | {{cache:SsmExecutionId>1}} |