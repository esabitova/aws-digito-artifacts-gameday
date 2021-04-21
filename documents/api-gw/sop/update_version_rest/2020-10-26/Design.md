# Id
api-gw:sop:update_version_rest:2020-10-26

## Intent
The script accepts given deployment id and applies it on the given stage. If deployment id is not set, the script tries
to find previous deployment (by creation date) and applies it on the stage.

## Type
Software Outage SOP

## Risk
Medium

## Requirements
* Existing REST API Gateway

## Permission required for AutomationAssumeRole
* apigateway:GET
* apigateway:PUT

## Supports Rollback
No.

## Inputs
### `AutomationAssumeRole`
  * type: String
  * description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf
### `RestApiGwId`
  * type: String
  * description: (Required) The ID of the REST API Gateway
### `RestStageName`
  * type: String
  * description: (Required) The stage name of the REST API Gateway
### `RestDeploymentId`
  * type: String
  * description: (Optional) The Id of deployment that should be applied on the give stage

## Details

1. `FindPreviousDeploymentIfNotProvided`
    * Type: aws:executeScript
    * Inputs:
        * `RestApiGwId`
        * `RestStageName`
        * `RestDeploymentId`
    * Outputs:
        * `RestDeploymentIdOriginalValue` returns `originalDeploymentId`
        * `RestDeploymentIdToApply` return either `RestDeploymentId` or `previousDeploymentId`
    * Explanation:
        * Find the current value of deployment id:
          * Execute [get_stage](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/apigateway.html#APIGateway.Client.get_stage)
            * Parameters:
              * `restApiId`='string'
              * `stageName`='string'
            * Return `.deploymentId` as `originalDeploymentId`
        * If `RestDeploymentId` is provided
          * Validate if provided deployment id and rest ip add up:
              *
              Execute [get_deployment](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/apigateway.html#APIGateway.Client.get_deployment):
                  * Parameters:
                      * `restApiId`=`RestApiGwId`
                      * `deploymentId`=`RestDeploymentId`
              * If no error and a record is returned, then return `RestDeploymentId` as an output and skip further
                actions of the current step. Otherwise, throw an error.
        * If `RestDeploymentId` is **NOT** provided, 
          * Get details of the current deployment:
            * Execute [get_deployment](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/apigateway.html#APIGateway.Client.get_deployment):
              * Parameters:
                * `restApiId`=`RestApiGwId`
                * `deploymentId`=`originalDeploymentId`
              * Return `.createdDate` as `currentDeploymentCreationDate`
          * Determine previous deployment based on creation date:
            * Execute [get_deployments](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/apigateway.html#APIGateway.Client.get_deployments):
                * Parameters:
                    * `restApiId`=`RestApiGwId`
                    * `position`=`take from the previous run of the current method`
                    * `limit`=500
                * Iterate over `.items` collection and find the latest deployment where `.items[].creationDate` less
                  than `currentDeploymentCreationDate`. If found, return as `previousDeploymentId`, otherwise throw an
                  error
1. `ChangeDeployment`
    * Type: aws:executeScript
    * Inputs:
        * `RestApiGwId`
        * `RestStageName`
    * Outputs:
        * `RestDeploymentIdNewValue`
    * Explanation:
        * Execute [update_stage](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/apigateway.html#APIGateway.Client.update_stage)
          * Parameters:
            * `restApiId`=`RestApiGwId`
            * `stageName`=`RestStageName`
            * `patchOperations`=`op='replace',path='/deploymentId',value='<FindPreviousDeploymentIfNotProvided.RestDeploymentIdToApply>'`
          * Return `.deploymentId`

## Outputs
* `FindPreviousDeploymentIfNotProvided.RestDeploymentIdOriginalValue`
* `FindPreviousDeploymentIfNotProvided.RestDeploymentIdToApply`
* `ChangeDeployment.RestDeploymentIdNewValue`