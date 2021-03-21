# Id
service1:test:your_test_name_with_underscores:yyyy-MM-dd

## Intent
* General description of what's going to be happen
* Special notes on validations happening inside if any
* Special notes on behavior in edge-cases if any
* Special notes on limitations and conditions of use if any

## Type
TBD: Software/AZ/Region/Hardware Outage Test

## Risk
TBD: High, Medium, Low

## Requirements
* Existing service1
* There is a synthetic alarm setup for application (e.g. <TBD: Example of what Alarm should be fired>)

## Permission required for AutomationAssumeRole
* TBD: service1:Action1

## Supports Rollback
Yes. Users can run the script with `IsRollback` and `PreviousExecutionId` to rollback changes from the previous run 

## Input
### `AutomationAssumeRole`
  * type: String
  * description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf
### `SyntheticAlarmName`:
  * type: String
  * description: (Required) Alarm which should be green after test
### `IsRollback`:
  * type: Boolean
  * description: (Optional) Run rollback step of the given previous execution (parameter `PreviousExecutionId`)
  * default: False
### `PreviousExecutionId`:
  * type: Integer
  * description: (Optional) The id of previous execution of the current script
  * default: 0
### TBD: `Parameter1`
  * type: String
  * description: (Required/Optional) You Awesome Description 
### TBD: `Parameter2`
  * type: String
  * description: (Required/Optional) You Awesome Description 

## Details of SSM Document steps:
1. `CheckIsRollback`
    * Type: aws:branch
    * Inputs:
        * `IsRollback`
    * Outputs: none
    * Explanation:
        * `IsRollback` it true, continue with `RollbackPreviousExecution` step
        * `IsRollback` it false, continue with `BackupThrottlingConfigurationAndInputs` step
1. `RollbackPreviousExecution`
    * Type: aws:executeScript
    * Inputs:
        * `PreviousExecutionId`
        * TBD: `OtherInputs`
    * Outputs: 
        * `<TBD:WhatHasBeenRestored>RestoredValue`
    * Explanation:
        * Take parameters from the previous execution with `PreviousExecutionId`
        * Compare *Inputs* and *params from the backup*, if not equal throw an error
        * Use *params from the backup* to restore value
        * isEnd: true
1. `Backup<TBD:WhatsGoingToBeBackedUp>gConfigurationAndInputs`
    * Type: aws:executeScript
    * Inputs:
        * TBD: `Inputs`
    * Outputs:
        * TBD: Returns all Inputs that identifies services under changes
        * TBD: All original values that changes in the current document 
    * Explanation:
        * TBD: Execute api, get something, etc.
1. `Set<TBD:WhatsGoingToBeSet>1`
    * Type: aws:executeScript
    * Inputs:
        * TBD: `Inputs`
    * Outputs: 
        * TBD: `<SomethingThatHasBenChanged>NewValue`
    * Explanation:
        * TBD
    * OnFailure: step: RollbackCurrentChanges 
1. `Set<TBD:WhatsGoingToBeSet>2`
    * Type: aws:executeScript
    * Inputs:
        * TBD: `Inputs`
    * Outputs: 
        * TBD: `<SomethingThatHasBenChanged>NewValue`
    * Explanation:
        * TBD
    * OnFailure: step: RollbackCurrentChanges 
1. `AssertAlarmToBeRed`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `SyntheticAlarmName`
    * Outputs: none
    * Explanation:
        * TBD
    * OnFailure: step: RollbackCurrentChanges 
1. `RollbackCurrentChanges`
    * Type: aws:executeScript
    * Inputs: none
    * Outputs:
        * `<WhatHasBeenRestored>RestoredValue`
    * Explanation:
        * Take all the values from `Backup<TBD:WhatsGoingToBeBackedUp>gConfigurationAndInputs`
1. `AssertAlarmToBeGreen`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `SyntheticAlarmName`
    * Outputs: none
    * Explanation:
        * Wait for `SyntheticAlarmName` alarm to be `OK` for `AlarmWaitTimeout` seconds
    * isEnd: true

## Outputs
* `Backup<TBD:WhatsGoingToBeBackedUp>gConfigurationAndInputs.<TBD:AllParametersFromBackup>`


if `IsRollback`:
* `RollbackPreviousExecution.<TBD:AllRestoredParameters>`

if not `IsRollback`:
* `Set<TBD:WhatsGoingToBeSet>.<TBD:AllNewParameters>`