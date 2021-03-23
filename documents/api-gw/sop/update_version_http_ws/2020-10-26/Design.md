# Id
api-gw:sop:update_version_http_ws:2020-10-26

## Intent
The scripts accepts given deployment id and applies it on the given stage. If deployment id is not set, the script tries to find previous deployment (by creation date) and applies it on the stage. 


## Type
Software Outage SOP

## Risk
Medium

## Requirements
* Existing HTTP or WEBSOCKET API Gateway

## Permission required for AutomationAssumeRole
* apigateway:GET
* apigateway:PUT

## Supports Rollback
No.

## Inputs
### `AutomationAssumeRole`
  * type: String
  * description: (Required) The ARN of the role that allows Automation to perform the actions on your behalf
### `HttpWsApiGwId`
  * type: String
  * description: (Required) The ARN of the API Gateway
### `HttpWsStageName`
  * type: String
  * description: (Required) The name of the stage where deployment version should be changed
### `HttpWsDeploymentId`
  * type: String
  * description: (Optional) The Id of deployment that should be applied on the give stage

## Details
1. `ValidateStage`
    * Type: aws:executeScript
    * Inputs:
        * `HttpWsApiGwId`
        * `HttpWsStageName`
    * Outputs: None
    * Explanation:
        * Check if auto deploy enabled on the given stage
          * Execute [get_stage](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/apigatewayv2.html#ApiGatewayV2.Client.get_stage)
            * Parameters:
              * `ApiId`=`HttpWsApiGwId`
              * `StageName`=`HttpWsStageName`
            * If `.AutoDeploy` is `True`, through an error saying that it's not possible to update deployment id for the given stage because of Auto Deploy is enabled.
1. `FindPreviousDeploymentIfNotProvided`
    * Type: aws:executeScript
    * Inputs:
        * `HttpWsApiGwId`
        * `HttpWsStageName`
        * `HttpWsDeploymentId`
    * Outputs:
      * `DeploymentIdToApply` - either `HttpWsDeploymentId` or `previousDeploymentId`
      * `DeploymentIdOriginalValue` - returns `originalDeploymentId`
    * Explanation:
        * Find the current deployment id for the given API and Stage
          * Execute [get_stage](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/apigatewayv2.html#ApiGatewayV2.Client.get_stage)
            * Parameters:
              * `ApiId`=`HttpWsApiGwId`
              * `StageName`=`HttpWsStageName`
            * Return `.DeploymentId` as `originalDeploymentId`
        * If `HttpWsDeploymentId` is provided:
          * Check if the given `HttpWsDeploymentId` relates to `HttpWsApiGwId`
            * Execute [get_deployments](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/apigatewayv2.html#ApiGatewayV2.Client.get_deployments)
              * Parameters:
                * `ApiId`=`HttpWsApiGwId`
              * Iterate over `.Items` array and find the most recent deployment where `.Items[].DeploymentId` == `HttpWsDeploymentId`.
                * If not found, return an error
                * If found, skip further steps and return `HttpWsDeploymentId` to the output
        * If `HttpWsDeploymentId` is **NOT** provided:
          * Get details of the current deployment 
            * Execute [get_deployment](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/apigatewayv2.html#ApiGatewayV2.Client.get_deployment)
              * Parameters:
                * `ApiId`=`HttpWsApiGwId`,
                * `DeploymentId`=`originalDeploymentId`
              * Return `.CreatedDate` as `originalDeploymentCreationDate`
          * Find the most recent deployment before `originalDeploymentCreationDate`
            * Execute [get_deployments](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/apigatewayv2.html#ApiGatewayV2.Client.get_deployments)
              * Parameters:
                * `ApiId`=`HttpWsApiGwId`
              * Iterate over `.Items` array and find the most recent deployment where `.Items[].CreationDate` < `originalDeploymentCreationDate`. Return `DeploymentId` as `previousDeploymentId`. If  nothing is found, throw an error

1. `ApplyDeploymentOnStage`
    * Type: aws:executeScript
    * Inputs:
        * `HttpWsApiGwId`
        * `HttpWsStageName`
    * Outputs:
        * `AppliedDeploymentId`
    * Explanation:
        * Update stage with a new deployment id:
          * Execute [update_stage](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/apigatewayv2.html#ApiGatewayV2.Client.update_stage)
            * Parameters:
              * `ApiId`=`HttpWsApiGwId`
              * `StageName`=`HttpWsStageName`
              * `DeploymentId`=`FindPreviousDeploymentIfNotProvided.DeploymentIdToApply`
            * Return `.DeploymentId` to the output
    * isEnd: true

## Outputs
* `FindPreviousDeploymentIfNotProvided.DeploymentIdToApply`
* `FindPreviousDeploymentIfNotProvided.DeploymentIdOriginalValue`
* `ApplyDeploymentOnStage.AppliedDeploymentId`