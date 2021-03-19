# Id
docdb:test:reboot_db_instance:2021-03-16

## Intent
Test DocDb cluster availability after rebooting the instance

## Type
DocDb failure test

## Risk
Small

## Requirements
* Available DocumentDB Cluster
* There is a synthetic alarm setup for application
* Application should be able to reconnect to db instance after temporary network errors.

## Permission required for AutomationAssumeRole
* rds:RebootDBInstance
* ssm:GetAutomationExecution
* ssm:StartAutomationExecution
* iam:PassRole

## Supports Rollback
No.

## Inputs
### DBInstanceIdentifier:
* type: String
* description: (Required) DocDb Instance Identifier
### SyntheticAlarmName:
* type: String
* description: (Required) Alarm which should be green after test.
### AutomationAssumeRole:
* type: String
* description:
  (Optional) The ARN of the role that allows Automation to perform
  the actions on your behalf. If no role is specified, Systems Manager Automation
  uses your IAM permissions to run this document.
  default: ''

## Document Steps:
1. aws:assertAwsResourceProperty - Assert alarm to be green before test
   * Inputs:
        * SyntheticAlarmName
2. aws:assertAwsResourceProperty - Assert DocDb instances are available
        * Inputs:
            * DBClusterIdentifier
3. aws:executeAutomation - Invoke SOP reboot_db_instance
        * Inputs:
            * DocumentName: Digito-RebootDbInstance_2020-09-21
            * RuntimeParameters:
                * DBInstanceIdentifier
                * AutomationAssumeRole
4. aws:waitForAwsResourceProperty - Wait for alarms to be green
        * Inputs:
            * SyntheticAlarmName
