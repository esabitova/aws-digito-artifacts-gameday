# coding=utf-8
"""SSM automation document to change REST API GW usage plan limits"""
from pytest_bdd import (
    scenario
)


@scenario('../features/update_version_ws.feature',
          'Run document for WS Api with a specified deployment Id')
def test_update_version_ws_specified():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/update_version_ws.feature',
          'Run document for WS Api for stage with AutoDeploy and expect failure as AutoDeploy is not supported')
def test_update_version_ws_autodeploy_on():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/update_version_ws.feature',
          'Run document for WS Api with provided deployment same as current')
def test_update_version_ws_specified_same_as_current():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/update_version_ws.feature',
          'Run document for WS Api without provided deployment Id')
def test_update_version_ws_not_specified():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/update_version_ws.feature',
          'Run document for WS Api without provided deployment Id and without available deployments')
def test_update_version_ws_no_deployments():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/update_version_ws.feature',
          'Run document for WS Api without provided deployment Id and without available previous deployments')
def test_update_version_ws_no_previous_deployments():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
