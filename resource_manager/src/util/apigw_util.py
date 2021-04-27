from boto3 import Session

from .boto3_client_factory import client
from .common_test_utils import assert_https_status_code_200, assert_https_status_code_less_or_equal


def create_deployment(session: Session, gateway_id: str, description: str = '') -> dict:
    """
    Use gateway_id and description to create a dummy deployment resource for test
    :param session: The boto3 client session
    :param gateway_id: The string identifier of the associated RestApi
    :param description: The description of deployment
    :return: apigw_client.create_deployment response
    """
    apigw_client = client('apigateway', session)
    response = apigw_client.create_deployment(restApiId=gateway_id, description=description)
    assert_https_status_code_less_or_equal(201, response, f'Failed to create deployment: {description}, '
                                                          f'restApiId: {gateway_id}')
    return response


def delete_deployment(session: Session, gateway_id: str, deployment_id: str) -> bool:
    """
    Use gateway_id and deployment_id to delete dummy deployment resource
    :param session: The boto3 client session
    :param gateway_id: The string identifier of the associated RestApi
    :param deployment_id: The ID of deployment to delete
    :return: True if successful
    """
    apigw_client = client('apigateway', session)
    response = apigw_client.delete_deployment(restApiId=gateway_id, deploymentId=deployment_id)
    assert_https_status_code_less_or_equal(202, response, f'Failed to delete deploymentId: {deployment_id}, '
                                                          f'restApiId: {gateway_id}')
    return True


def get_stage(session: Session, gateway_id: str, stage_name: str) -> dict:
    """
    Use gateway_id and stage_name to get information about the Stage resource and return it as a dict
    :param session: The boto3 client session
    :param gateway_id: The string identifier of the associated RestApi
    :param stage_name: The name of the Stage resource to get information about
    :return: apigw_client.get_stage response
    """
    apigw_client = client('apigateway', session)
    response = apigw_client.get_stage(restApiId=gateway_id, stageName=stage_name)
    assert_https_status_code_200(response, f'Failed to perform get_stage with '
                                           f'restApiId: {gateway_id} and stageName: {stage_name}')
    return response


def update_stage_deployment(session: Session, gateway_id: str, stage_name: str, deployment_id: str) -> dict:
    """
    Use gateway_id, stage_name and deployment_id to update the Stage resource.
    :param session: The boto3 client session
    :param gateway_id: The string identifier of the associated RestApi
    :param stage_name: The name of the Stage resource to get information about
    :param deployment_id The Deployment ID to apply to Stage resource
    :return: apigw_client.update_stage response
    """
    apigw_client = client('apigateway', session)
    response = apigw_client.update_stage(
        restApiId=gateway_id,
        stageName=stage_name,
        patchOperations=[
            {
                'op': 'replace',
                'path': '/deploymentId',
                'value': deployment_id,
            },
        ]
    )
    assert_https_status_code_200(response, f'Failed to perform update_stage with restApiId: {gateway_id},'
                                           f' stageName: {stage_name} and deploymentId: {deployment_id}')
    return response
