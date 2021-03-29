# Id
nat-gw:test:simulate_internet_unavailable:2020-09-21

## Intent
Test behavior of resources that require internet access

## Type
AZ Outage Test

## Risk
High

## Requirements
* NAT Gateway
* IGW
* VPC
* Public Subnet
* Private Subnet
* Route Table associated with the private subnet
* Route with target the Nat Gateway

## Permission required for AutomationAssumeRole
* ec2:DescribeRouteTables
* ec2:DeleteRoute
* ec2:CreateRoute
* ec2:DescribeSubnets
* cloudwatch:DescribeAlarms

## Supports Rollback
Yes.

* Explanation: The rollback consists of updating the private subnet route table to the previous state by adding the Nat Gateway route when the specified alarms fires (e.g. PacketsOutToDestination metric alarm). Customers can run the script with `IsRollback` and `PreviousExecutionId` to rollback changes from the previous run

## Inputs

### PrivateSubnetId
* Type: String
* Description: (Optional) The Private Subnet ID.
### NatGatewayId
* Type: String
* Description: (Required) The NAT Gateway ID
### AutomationAssumeRole
* Type: String
* Description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf. See Permissions required above for test.
### SyntheticAlarmName
* Type: String 
* Description: (Required) Alarm which should be green after test.
### IsRollback:
* type: String
* description: (Optional) Provide true to cleanup appliance created in previous execution. Can be either true or false.
* default: False
### PreviousExecutionId:
* type: String
* description: (Optional) Previous execution id for which resources need to be cleaned up.
* default: ''

## Details of SSM Document steps:

1. `CheckIsRollback`
    * Type: aws:branch
    * Inputs:
        * `IsRollback`
    * Outputs: none
    * Explanation:
        * If `IsRollback` is true, go to the step `RollbackPreviousExecution`. 
        * If `IsRollback` is false, proceed to the step `BackupPrivateSubnetRouteTableNATGatewayRouteAndInputs`

1. `RollbackPreviousExecution`:
    * Type: aws:executeScript
    * Inputs:
        * `PreviousExecutionId`: The id of the previous execution which has to be rolled back to the initial state.
        * `PrivateSubnetId`
        * `NatGatewayId`
    * Outputs:
        * `DestinationCidrBlockAndRouteTableIdMappingListRestoredValue`:  The collection of mappings between Destination Cidr block and Route Table Id.
    * Explanation:
        * Get values from the previous execution using `PreviousExecutionId`
            * `BackupPrivateSubnetRouteTableNATGatewayRouteAndInputs.NatGatewayId`
            * `BackupPrivateSubnetRouteTableNATGatewayRouteAndInputs.PrivateSubnetId`
            * `BackupPrivateSubnetRouteTableNATGatewayRouteAndInputs.DestinationCidrBlockAndRouteTableIdMappingListOriginalValue`
        * Validate if `PrivateSubnetId` and `BackupPrivateSubnetRouteTableNATGatewayRouteAndInputs.PrivateSubnetId` are equal. Thrown an error if not
        * Validate if `NatGatewayId` and `BackupPrivateSubnetRouteTableNATGatewayRouteAndInputs.NatGatewayId` are equal. Thrown an error if not
        * Iterate over `BackupPrivateSubnetRouteTableNATGatewayRouteAndInputs.DestinationCidrBlockAndRouteTableIdMappingListOriginalValue`
            * Call [create_route](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.create_route) 
                * Parameters:
                    * `RouteTableId`=`<Value from mapping elements>`
                    * `DestinationCidrBlock`=`<Value from mapping elements>`
                    * `NatGatewayId`=`BackupPrivateSubnetRouteTableNATGatewayRouteAndInputs.NatGatewayId`
        * Execute [describe_route_tables](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_route_tables)
            * if `PrivateSubnetId` provided:
                * Parameters:
                    * `Filters`=`association.subnet-id=<PrivateSubnetId>,route.nat-gateway-id=<NatGatewayId>`
            * if `PrivateSubnetId` **NOT** provided:
                * Parameters:
                    * `Filters`=`route.nat-gateway-id=<NatGatewayId>`
            * Filter out the response using `BackupPrivateSubnetRouteTableNATGatewayRouteAndInputs.DestinationCidrBlockAndRouteTableIdMappingListOriginalValue`, `PrivateSubnetId` and `NatGatewayId` and return similar mapping using:
                * `.RouteTables[].Routes[].DestinationCidrBlock`
                * `.RouteTables[].RouteTableId`
    * isEnd: true

1. `BackupPrivateSubnetRouteTableNATGatewayRouteAndInputsAndInputs`
    * Type: aws:executeScript
    * Inputs:
        * `PrivateSubnetId`: pass the `PrivateSubnetId` parameter
        * `NatGatewayId`: pass the `NatGatewayId` parameter
    * Outputs:
        * `NatGatewayId`: The NAT Gateway ID
        * `DestinationCidrBlockAndRouteTableIdMappingListOriginalValue`: The collection of mappings between Destination Cidr block and Route Table Id.
        * `PrivateSubnetId`: The input parameter
    * Explanation:
        * Find route to an NAT GW 
            * Execute [describe_route_tables](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_route_tables)
                * if `PrivateSubnetId` provided:
                    * Parameters:
                        * `Filters`=`association.subnet-id=<PrivateSubnetId>,route.nat-gateway-id=<NatGatewayId>`
                    * Find the first route. Return as collection of mappings (example: `[{"route_table_id":"ABC", "dst_cidr":"10.0.1.0/26"}]`)
                        * `.RouteTables[].RouteTableId` 
                        * `.RouteTables[].Routes[].DestinationCidrBlock`
                * if `PrivateSubnetId` **NOT** provided:
                    * Parameters:
                        * `Filters`=`route.nat-gateway-id=<NatGatewayId>`
                    * Take response as `DescribeRouteTablesResponse`
                    * Build response:
                        * Get all subnet Ids and determine AZ:
                            * Get all `.RouteTables[].Associations[].SubnetId`
                            * Call [describe_subnets](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_subnets)
                                * Parameters:
                                    * `SubnetIds`=`<List of Subnet Ids>`
                                * Group by subnets by `.Subnets[].AvailabilityZone` and return list of subnets in one random AZ as `ListOfSubnetsIdInOneAz`
                        * Filter out `DescribeRouteTablesResponse` using `ListOfSubnetsIdInOneAz` by `.RouteTables[].Associations[].SubnetId`
                        * Use filtered collection build a collection of mappings (example: `[{"route_table_id":"ABC", "dst_cidr":"10.0.1.0/26"}]`) using the following values:
                            * `.RouteTables[].RouteTableId` 
                            * `.RouteTables[].Routes[].DestinationCidrBlock`

1. `DeletePrivateSubnetRouteTableNATGatewayRoute`
    * Type: aws:executeScript
    * Inputs: none
    * Outputs: 
        * `DestinationCidrBlockAndRouteTableIdMappingListUpdatedValue`
    * Explanation:
        * Iterate over `BackupPrivateSubnetRouteTableNATGatewayRouteAndInputs.DestinationCidrBlockAndRouteTableIdMappingListOriginalValue`:
            * Delete the private subnet route table route
                * Call [delete_route](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.delete_route) 
                    * Parameters:
                        * `RouteTableId`=`<Value from the mapping>`
                        * `DestinationCidrBlock`=`<Value from the mapping>`
        * Get updated state of the route table
            * Execute [describe_route_tables](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_route_tables)
                * if `PrivateSubnetId` provided:
                    * Parameters:
                        * `Filters`=`association.subnet-id=<BackupPrivateSubnetRouteTableNATGatewayRouteAndInputs.PrivateSubnetId>,route.nat-gateway-id=<BackupPrivateSubnetRouteTableNATGatewayRouteAndInputs.NatGatewayId>`
                * if `PrivateSubnetId` **NOT** provided:
                    * Parameters:
                        * `Filters`=`route.nat-gateway-id=<BackupPrivateSubnetRouteTableNATGatewayRouteAndInputs.NatGatewayId>`
                * Filter out the response by `RouteTableId[]` from `BackupPrivateSubnetRouteTableNATGatewayRouteAndInputs.DestinationCidrBlockAndRouteTableIdMappingListOriginalValue`. Mapping of route tables and routes (example:`[{"route_table_id":"ABC", "dst_cidr":"10.0.1.0/26"}]`). Use:
                    * `.RouteTables[].RouteTableId`
                    * `.RouteTables[].Routes[].DestinationCidrBlock`

1. `AssertAlarmToBeRed`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `Service`: cloudwatch
        * `Api`: DescribeAlarms
        * `AlarmNames`: pass SyntheticAlarmName parameter in a list
    * Outputs: none
    * Explanation:
        * Wait for `SyntheticAlarmName` alarm to be ALARM for `AlarmWaitTimeout` seconds. [describe_alarms](https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/API_DescribeAlarms.html) method
    * OnFailure: go to step `RollbackCurrentExecution`

1. `RollbackCurrentExecution` 
    * Type: aws:executeScript
    * Inputs: none
    * Outputs: 
        * `DestinationCidrBlockAndRouteTableIdMappingListRestoredValue`:  The collection of mappings between Destination Cidr block and Route Table Id.
    * Explanation:
        * Iterate over `BackupPrivateSubnetRouteTableNATGatewayRouteAndInputs.DestinationCidrBlockAndRouteTableIdMappingListOriginalValue`:
            * Call [create_route](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.create_route) 
                * Parameters:
                    * `NatGatewayId`=`BackupPrivateSubnetRouteTableNATGatewayRouteAndInputs.NatGatewayId`
                    * `RouteTableId`=`<Value from mapping>`
                    * `DestinationCidrBlock=`=`<Value from mapping>`
        * Get updated state of the route table
            * Execute [describe_route_tables](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_route_tables)
                * if `PrivateSubnetId` provided:
                    * Parameters:
                        * `Filters`=`association.subnet-id=<BackupPrivateSubnetRouteTableNATGatewayRouteAndInputs.PrivateSubnetId>,route.nat-gateway-id=<BackupPrivateSubnetRouteTableNATGatewayRouteAndInputs.NatGatewayId>`
                * if `PrivateSubnetId` **NOT** provided:
                    * Parameters:
                        * `Filters`=`route.nat-gateway-id=<BackupPrivateSubnetRouteTableNATGatewayRouteAndInputs.NatGatewayId>`
                * Filter out the response by `RouteTableId[]` from `BackupPrivateSubnetRouteTableNATGatewayRouteAndInputs.DestinationCidrBlockAndRouteTableIdMappingListOriginalValue`. Mapping of route tables and routes (example:`[{"route_table_id":"ABC", "dst_cidr":"10.0.1.0/26"}]`). Use:
                    * `.RouteTables[].RouteTableId`
                    * `.RouteTables[].Routes[].DestinationCidrBlock`
        
1. `AssertAlarmToBeGreen`
    * Type: aws:waitForAwsResourceProperty
    * Inputs:
        * `Service`: cloudwatch
        * `Api`: DescribeAlarms
        * `AlarmNames`: pass SyntheticAlarmName parameter in a list
    * Outputs: none
    * Explanation:
        * Wait for `SyntheticAlarmName` alarm to be OK for `AlarmWaitTimeout` seconds. [describe_alarms](https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/API_DescribeAlarms.html) method
    * isEnd: true

## Outputs
If `IsRollback`:
* `RollbackPreviousExecution.DestinationCidrBlockAndRouteTableIdMappingListRestoredValue`

If not `IsRollback`:
* `BackupPrivateSubnetRouteTableNATGatewayRouteAndInputsAndInputs.NatGatewayId`
* `BackupPrivateSubnetRouteTableNATGatewayRouteAndInputsAndInputs.PrivateSubnetId`
* `BackupPrivateSubnetRouteTableNATGatewayRouteAndInputsAndInputs.DestinationCidrBlockAndRouteTableIdMappingListOriginalValue`

* `DeletePrivateSubnetRouteTableNATGatewayRoute.DestinationCidrBlockAndRouteTableIdMappingListUpdatedValue`

* `RollbackCurrentExecution.DestinationCidrBlockAndRouteTableIdMappingListRestoredValue`


