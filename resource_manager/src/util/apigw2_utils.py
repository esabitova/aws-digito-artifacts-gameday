from boto3 import Session

from .boto3_client_factory import client
from .common_test_utils import assert_https_status_code_200, assert_https_status_code_less_or_equal


def create_deployment(session: Session, gateway_id: str, description: str = '') -> dict:
    """
    Use gateway_id and description to create a dummy deployment resource for test
    :param session: The boto3 client session
    :param gateway_id: The string identifier of the associated Gateway API
    :param description: The description of deployment
    :return: apigw2_client.create_deployment response
    """
    apigw2_client = client('apigatewayv2', session)
    response = apigw2_client.create_deployment(ApiId=gateway_id, Description=description)
    assert_https_status_code_less_or_equal(201, response, f'Failed to create deployment: {description}, '
                                                          f'ApiId: {gateway_id}')
    return response


def delete_deployment(session: Session, gateway_id: str, deployment_id: str) -> bool:
    """
    Use gateway_id and deployment_id to delete dummy deployment resource
    :param session: The boto3 client session
    :param gateway_id: The string identifier of the associated Gateway API
    :param deployment_id: The ID of deployment to delete
    :return: True if successful
    """
    apigw2_client = client('apigatewayv2', session)
    response = apigw2_client.delete_deployment(ApiId=gateway_id, DeploymentId=deployment_id)
    assert_https_status_code_less_or_equal(204, response, f'Failed to delete DeploymentId: {deployment_id}, '
                                                          f'ApiId: {gateway_id}')
    return True


def get_stage(session: Session, gateway_id: str, stage_name: str) -> dict:
    """
    Use gateway_id and stage_name to get information about the Stage resource and return it as a dict
    :param session: The boto3 client session
    :param gateway_id: The string identifier of the associated Gateway API
    :param stage_name: The name of the Stage resource to get information about
    :return: apigw_client2.get_stage response
    """
    apigw2_client = client('apigatewayv2', session)
    response = apigw2_client.get_stage(ApiId=gateway_id, StageName=stage_name)
    assert_https_status_code_200(response, f'Failed to perform get_stage with '
                                           f'ApiId: {gateway_id} and StageName: {stage_name}')
    return response


def update_stage_deployment(session: Session, gateway_id: str, stage_name: str, deployment_id: str) -> dict:
    """
    Use gateway_id, stage_name and deployment_id to update the Stage resource.
    :param session: The boto3 client session
    :param gateway_id: The string identifier of the associated Gateway API
    :param stage_name: The name of the Stage resource to set deployment for
    :param deployment_id The Deployment ID to apply to Stage resource
    :return: apigw2_client.update_stage response
    """
    apigw2_client = client('apigatewayv2', session)
    response = apigw2_client.update_stage(
        ApiId=gateway_id,
        StageName=stage_name,
        DeploymentId=deployment_id
    )
    assert_https_status_code_200(response, f'Failed to perform update_stage with ApiId: {gateway_id},'
                                           f' StageName: {stage_name} and DeploymentId: {deployment_id}')
    return response


def get_default_throttling_settings(session: Session, gateway_id: str, stage_name: str):
    stage_default_settings = get_stage(session, gateway_id, stage_name)['DefaultRouteSettings']
    if 'ThrottlingRateLimit' not in stage_default_settings or 'ThrottlingBurstLimit' not in stage_default_settings:
        # If throttling is not enabled use account level limits
        service_quota_client = client('service-quotas', session)
        quota_rate_limit_code: str = 'L-8A5B8E43'
        quota_burst_limit_code: str = 'L-CDF5615A'

        quota_rate_limit: float = service_quota_client.get_service_quota(
            ServiceCode='apigateway', QuotaCode=quota_rate_limit_code
        )['Quota']['Value']
        quota_burst_limit: float = service_quota_client.get_service_quota(
            ServiceCode='apigateway', QuotaCode=quota_burst_limit_code
        )['Quota']['Value']
    else:
        quota_rate_limit = stage_default_settings['ThrottlingRateLimit']
        quota_burst_limit = stage_default_settings['ThrottlingBurstLimit']
    return {'ThrottlingRateLimit': quota_rate_limit, 'ThrottlingBurstLimit': int(quota_burst_limit)}


def get_route_throttling_settings(session: Session, gateway_id: str, stage_name: str, route_key: str):
    route_settings = get_stage(session, gateway_id, stage_name)['RouteSettings']
    if route_key not in route_settings or 'ThrottlingRateLimit' not in route_settings[route_key] \
            or 'ThrottlingBurstLimit' not in route_settings[route_key]:
        return {'ThrottlingRateLimit': False, 'ThrottlingBurstLimit': False}
    else:
        quota_rate_limit = route_settings[route_key]['ThrottlingRateLimit']
        quota_burst_limit = route_settings[route_key]['ThrottlingBurstLimit']
        return {'ThrottlingRateLimit': quota_rate_limit, 'ThrottlingBurstLimit': int(quota_burst_limit)}


def update_default_throttling_settings(
        session: Session, gateway_id: str, stage_name: str, rate_limit: str, burst_limit: str
) -> dict:
    """
    Set stage default route throttling settings
    :param session: The boto3 client session
    :param gateway_id: The string identifier of the associated Gateway API
    :param stage_name: The name of the Stage resource to set values for
    :param rate_limit: Value for ThrottlingRateLimit
    :param burst_limit: Value for ThrottlingBurstLimit
    :return: apigw2_client.update_stage response
    """
    apigw2_client = client('apigatewayv2', session)
    stage_default_settings = get_stage(session, gateway_id, stage_name)['DefaultRouteSettings']
    stage_default_settings['ThrottlingBurstLimit'] = burst_limit
    stage_default_settings['ThrottlingRateLimit'] = rate_limit

    response = apigw2_client.update_stage(
        ApiId=gateway_id,
        StageName=stage_name,
        DefaultRouteSettings=stage_default_settings
    )
    assert_https_status_code_200(response, f'Failed to perform update_stage with ApiId: {gateway_id}'
                                           f' and StageName: {stage_name}')
    return response


def update_route_throttling_settings(
        session: Session, gateway_id: str, stage_name: str, route_key: str, rate_limit: int, burst_limit: int
) -> dict:
    """
    Set stage default route throttling settings
    :param session: The boto3 client session
    :param gateway_id: The string identifier of the associated Gateway API
    :param stage_name: The name of the Stage resource to set values for
    :param route_key: The key of the route to set values for
    :param rate_limit: Value for ThrottlingRateLimit
    :param burst_limit: Value for ThrottlingBurstLimit
    :return: apigw2_client.update_stage response
    """
    apigw2_client = client('apigatewayv2', session)
    stage_route_settings = get_stage(session, gateway_id, stage_name)['RouteSettings']
    if route_key not in stage_route_settings:
        stage_route_settings[route_key] = {}
    stage_route_settings[route_key]['ThrottlingBurstLimit'] = burst_limit
    stage_route_settings[route_key]['ThrottlingRateLimit'] = rate_limit

    response = apigw2_client.update_stage(
        ApiId=gateway_id,
        StageName=stage_name,
        RouteSettings=stage_route_settings
    )
    assert_https_status_code_200(response, f'Failed to perform update_stage with ApiId: {gateway_id}'
                                           f' and StageName: {stage_name}')
    return response
