@efs @integration @alarm
Feature: Alarm Setup - EFS ClientConnections
  Scenario: Lease EFS from resource manager and test attach an alarm from Document
    Given the cloud formation templates as integration test resources
      |CfnTemplatePath                                                    | ResourceType |
      |resource_manager/cloud_formation_templates/EFSTemplate.yml         | ON_DEMAND    |
    When alarm "efs:alarm:client_connections:2020-04-01" is installed
      |FileSystem                       | Threshold | AlarmName           |
      |{{cfn-output:EFSTemplate>EFSID}} | 1         | EFSClientConnection |
    Then assert metrics for all alarms are populated

