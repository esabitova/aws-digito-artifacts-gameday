# coding=utf-8

from pytest_bdd import (
    scenario
)


@scenario('../features/update_version_rest.feature',
          'Run document with provided RestDeploymentId')
def test_update_version_rest_with_provided_deployment_id():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/update_version_rest.feature',
          'Run document with provided RestDeploymentId same as current deployment')
def test_update_version_rest_with_provided_deployment_id_same_as_current():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/update_version_rest.feature',
          'Run document without provided RestDeploymentId')
def test_update_version_rest_without_provided_deployment_id():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/update_version_rest.feature',
          'Run document without provided RestDeploymentId and without available deployments for update')
def test_update_version_rest_without_provided_deployment_id_and_without_available_deployments():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/update_version_rest.feature',
          'Run document without provided RestDeploymentId and without previous deployments for update')
def test_update_version_rest_without_provided_deployment_id_and_without_previous_deployments():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
