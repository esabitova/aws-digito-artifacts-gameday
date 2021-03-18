# Id
api-gw:test:simulate_network_unavailable:2020-09-21

## Intent
Test REST API Gateway with binding to VPC behavior when security groups are misconfigured. Since API VPC endpoints is not accessible due to certain security groups we can expected bringing down the number of API calls and corresponding alarms fired 

## Type
AZ Outage Test, Region Outage Test

## Risk
High

## Requirements
* Existing REST API Gateway with binding to VPC
* There is a synthetic alarm setup for application (api-gw:alarm:count:2020-04-01)

## Permission required for AutomationAssumeRole
* ec2:ModifyVpcEndpoint
* ec2:DescribeVpcEndpoints
* apigateway:GET

## Supports Rollback
Yes. Users can run the script with `IsRollback` and `PreviousExecutionId` to rollback changes from the previous run 

## Input
### `AutomationAssumeRole`
  * type: String
  * description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf
### `SyntheticAlarmName`:
  * type: String
  * description: (Required) Alarm which should be green after test
### `AlarmWaitTimeout`
  * type: Integer
  * description: (Optional) Alarm wait timeout
  * default: 300 (seconds)
### `RestApiGwId`
  * type: String
  * description: (Required) The Id of the REST API Gateway
### `SecurityGroupIdListToUnassign`
  * type: List
  * description: (Optional) The list of Security Group Ids that should be unassigned from the the API. If not provided, all Security Groups will be unassigned from attached VPC endpoints
### `IsRollback`:
  * type: Boolean
  * description: (Optional) Run rollback step of the given previous execution (parameter `PreviousExecutionId`)
  * default: False
### `PreviousExecutionId`:
  * type: Integer
  * description: (Optional) The id of previous execution of the current script
  * default: 0

## Details of SSM Document steps:
1. `CheckIsRollback`
    * Type: aws:branch
    * Inputs:
        * `IsRollback`
    * Outputs: none
    * Explanation:
        * `IsRollback` it true, continue with `RollbackPreviousExecution` step
        * `IsRollback` it false, continue with `BackupSecurityGroupConfigurationAndInputs` step
1. `RollbackPreviousExecution`
    * Type: aws:executeScript
    * Inputs:
        * `PreviousExecutionId`
    * Outputs: 
        * `VpcEndpointsSecurityGroupsMappingRestoredValue` - a JSON like `{"VPCEndpointID1":[SecurityGroupsList1],"VPCEndpointID2":[SecurityGroupsList2]}`

        Values from previous execution:
        * `BackupSecurityGroupConfigurationAndInputs.VpcEndpointsSecurityGroupsToBeRemoved`
        * `BackupSecurityGroupConfigurationAndInputs.VpcEndpointsSecurityGroupsMappingOriginalValue`
        * `BackupSecurityGroupConfigurationAndInputs.RestApiGwId`
        * `BackupSecurityGroupConfigurationAndInputs.SecurityGroupIdListToUnassign`
    * Explanation:
        * Get values from `BackupSecurityGroupConfigurationAndInputs` of the previous execution `PreviousExecutionId`
        * Take VPC endpoints from `BackupSecurityGroupConfigurationAndInputs.VpcEndpointsSecurityGroupsToBeRemoved` 
        * For each VPC endpoint execute https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.modify_vpc_endpoint with the following parameters:
            * `AddSecurityGroupIds`=[`BackupSecurityGroupConfigurationAndInputs.SecurityGroupIdListToUnassign` if `BackupSecurityGroupConfigurationAndInputs.SecurityGroupIdListToUnassign` defined, else use mapped security groups from `BackupSecurityGroupConfigurationAndInputs.VpcEndpointsSecurityGroupsToBeRemoved` ]
        * Get list security groups assigned for each VPC Endpoint. Execute https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_vpc_endpoints with the following parameters:
            * `VpcEndpointIds`=[*`BackupSecurityGroupConfigurationAndInputs.VpcEndpointsSecurityGroupsToBeRemoved`]
        * Return a mapping between VPC endpoints and updated list of security groups
        * isEnd: true
1. `BackupSecurityGroupConfigurationAndInputs`
    * Type: aws:executeScript
    * Inputs:
        * `RestApiGwId`
        * `SecurityGroupIdListToUnassign`
    * Outputs:
        * `VpcEndpointsSecurityGroupsToBeRemoved` - list of VPC endpoints where `SecurityGroupIdListToUnassign` is assigned to
        * `VpcEndpointsSecurityGroupsMappingOriginalValue` - a JSON like `{"VPCEndpointID1":[SecurityGroupsList1],"VPCEndpointID2":[SecurityGroupsList2]}`. This value is not going to be used by the script, mostly it's for end users' information
        * `RestApiGwId`
        * `SecurityGroupIdListToUnassign`
    * Explanation:
        * Get VPC Endpoint Id by executing https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/apigateway.html#APIGateway.Client.get_rest_api with the following parameters:
            * `restApiId`=`RestApiGwId`
        * Find `endpointConfiguration.vpcEndpointIds`
        * Get list security groups assigned for each VPC Endpoint. Execute https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_vpc_endpoints with the following parameters:
            * `VpcEndpointIds`=[`List of VPC endpoint IDs from the previous step`]
        * Return the list of VPC endpoints **only which that have SGs that are in  `SecurityGroupIdListToUnassign`**. If `SecurityGroupIdListToUnassign` is not provided, take all VPC endpoints and SGs with them
        * Return a mapping between VPC and updated list of security groups (**only which that have SGs that are in  `SecurityGroupIdListToUnassign`to**). If `SecurityGroupIdListToUnassign` is not provided, take all VPC endpoints and SGs with them
1. `UpdateSecurityGroups`
    * Type: aws:executeScript
    * Inputs:
        * `RestApiGwId`
        * `SecurityGroupIdListToUnassign`
    * Outputs: 
        * `VpcEndpointsSecurityGroupsMappingNewValue` - a JSON like `{"VPCEndpointID1":[SecurityGroupsList1],"VPCEndpointID2":[SecurityGroupsList2]}`
    * Explanation:
        * Take VPC endpoints from `BackupSecurityGroupConfigurationAndInputs.VpcEndpointsSecurityGroupsToBeRemoved` 
        * For each VPC endpoint in `BackupSecurityGroupConfigurationAndInputs.VpcEndpointsSecurityGroupsMappingOriginalValue` execute https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.modify_vpc_endpoint with the following parameters:
            * `RemoveSecurityGroupIds`=[`SecurityGroupIdListToUnassign` if `SecurityGroupIdListToUnassign` is provided, else take value from mapping in `BackupSecurityGroupConfigurationAndInputs.VpcEndpointsSecurityGroupsToBeRemoved` (Remove all groups)]
        * Validate that response is `{"Return": True}`
        * Execute https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_vpc_endpoints with the following parameters:
            * `VpcEndpointIds`=[*`BackupSecurityGroupConfigurationAndInputs.VpcEndpointsSecurityGroupsToBeRemoved`]
        * Return a mapping between VPC endpoints and updated list of security groups
    * OnFailure: step: RollbackCurrentChanges 
1. `AssertAlarmToBeRed`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `SyntheticAlarmName`
        * `AlarmWaitTimeout`
    * Outputs: none
    * Explanation:
        * Wait for `SyntheticAlarmName` alarm to be `ALARM` for `AlarmWaitTimeout` seconds
    * OnFailure: step: RollbackCurrentChanges 
1. `RollbackCurrentChanges`
    * Type: aws:executeScript
    * Inputs:
        * `BackupSecurityGroupConfigurationAndInputs.VpcEndpointsSecurityGroupsToBeRemoved`
    * Outputs:
        * `VpcEndpointsSecurityGroupsMappingRestoredValue` - a JSON like `{"VPCEndpointID1":[SecurityGroupsList1],"VPCEndpointID2":[SecurityGroupsList2]}`
    * Explanation:
        * Take VPC endpoints from `BackupSecurityGroupConfigurationAndInputs.VpcEndpointsSecurityGroupsToBeRemoved` of the current execution
        * For each VPC endpoint execute https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.modify_vpc_endpoint with the following parameters:
            * `AddSecurityGroupIds`=[`BackupSecurityGroupConfigurationAndInputs.SecurityGroupIdListToUnassign` if `BackupSecurityGroupConfigurationAndInputs.SecurityGroupIdListToUnassign` defined, else use mapped security groups from `BackupSecurityGroupConfigurationAndInputs.VpcEndpointsSecurityGroupsToBeRemoved` ]
        * Execute https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_vpc_endpoints with the following parameters:
            * `VpcEndpointIds`=[*`BackupSecurityGroupConfigurationAndInputs.VpcEndpointsSecurityGroupsToBeRemoved`]
        * Return a mapping between VPC and updated list of security groups
1. `AssertAlarmToBeGreen`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `SyntheticAlarmName`
        * `AlarmWaitTimeout`
    * Outputs: none
    * Explanation:
        * Wait for `SyntheticAlarmName` alarm to be `OK` for `AlarmWaitTimeout` seconds
    * isEnd: true
    
## Outputs
if `IsRollback`:
* `RollbackPreviousExecution.VpcEndpointsSecurityGroupsToBeRemoved`
* `RollbackPreviousExecution.VpcEndpointsSecurityGroupsMappingOriginalValue`
* `RollbackPreviousExecution.RestApiGwId`
* `RollbackPreviousExecution.SecurityGroupIdListToUnassign`
* `RollbackPreviousExecution.VpcEndpointsSecurityGroupsMappingRestoredValue`

if not `IsRollback`:
* `BackupSecurityGroupConfigurationAndInputs.VpcEndpointsSecurityGroupsToBeRemoved`
* `BackupSecurityGroupConfigurationAndInputs.VpcEndpointsSecurityGroupsMappingOriginalValue`
* `BackupSecurityGroupConfigurationAndInputs.RestApiGwId`
* `BackupSecurityGroupConfigurationAndInputs.SecurityGroupIdListToUnassign`
* `UpdateSecurityGroups.VpcEndpointsSecurityGroupsMappingNewValue`
* `RollbackCurrentChanges.VpcEndpointsSecurityGroupsMappingRestoredValue`