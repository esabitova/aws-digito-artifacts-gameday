# coding=utf-8

from pytest_bdd import (
    scenario
)


@scenario('../features/update_version_rest.feature',
          'Accept given deployment id and applies it on the given stage with provided RestDeploymentId v2')
def test_update_version_rest_with_provided_deployment_id_v2():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/update_version_rest.feature',
          'Accept given deployment id and applies it on the given stage with provided RestDeploymentId v1')
def test_update_version_rest_with_provided_deployment_id_v1():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/update_version_rest.feature',
          'Accept given deployment id and applies it on the given stage with provided RestDeploymentId same as current')
def test_update_version_rest_with_provided_deployment_id_same_as_current():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
