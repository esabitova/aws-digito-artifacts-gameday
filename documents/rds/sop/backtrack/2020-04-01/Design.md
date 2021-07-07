# Id
rds:sop:backtrack:2020-04-01

## Intent
SOP from Digito to backtrack an RDS Aurora cluster.

## Type
Software

## Risk
Small

## Requirements
* Aurora Cluster

## Permission required for AutomationAssumeRole
* rds:BacktrackDBCluster
* rds:DescribeDBClusters
* rds:DescribeDBClusterBacktracks

## Supports Rollback
No.

## Inputs


### DbClusterIdentifier
  * Description: (Required) The identifier for the db cluster
  * Type: String
### BacktrackTo
  * Description: (Required) An ISO 8601 date and time
  * Type: String
### AutomationAssumeRole:
  * Description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf.
  * Type: String
  
## Outputs
  * `OutputRecoveryTime.RecoveryTime`: recovery time in seconds

## Details of SSM Document steps:
1. `RecordStartTime`
    * Type: aws:executeScript
    * Outputs:
        * `StartTime`
    * Explanation:
        * Start the timer when SOP starts
2. `BacktracDb`
   * Type: aws:executeAwsApi
   * Inputs:
      * `DBClusterIdentifier`
      * `BacktrackTo`
   * Explanation:
       * Backtracks the Cluster to BacktrackTo date [BacktrackDBCluster](https://docs.aws.amazon.com/AmazonRDS/latest/APIReference/API_BacktrackDBCluster.html)
3. `WaitUntilInstancesAvailable`
    * Type: aws:waitForAwsResourceProperty
    * Api: DescribeDBClusterBacktracks
    * Inputs:
        * `DBClusterIdentifier`
    * PropertySelector: `$.DBClusterBacktracks[0].Status`
    * DesiredValues: `COMPLETED`, `FAILED`
    * Explanation:
        * Wait until backtracking is done or failed
4. `VerifyBacktrackSuccess`
    * Type: aws:assertAwsResourceProperty
    * Api: DescribeDBClusterBacktracks
    * Inputs:
        * `DBClusterIdentifier`
    * PropertySelector: `$.DBClusterBacktracks[0].Status`
    * DesiredValues: `COMPLETED`
    * Explanation:
        * Assert backtracking is successful    
5. `OutputRecoveryTime`
    * Type: aws:executeScript
    * Inputs:
        * `RecordStartTime.StartTime`
    * Outputs:
        * `RecoveryTime`
    * Explanation:
        * Measures recovery time
