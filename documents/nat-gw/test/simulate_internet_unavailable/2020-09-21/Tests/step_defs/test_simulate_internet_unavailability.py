# coding=utf-8

from pytest_bdd import (
    scenario
)


@scenario('../features/simulate_internet_unavailability.feature',
          'Simulate internet unavalability through changing route to NAT GW '
          'when customer specified only NatGatewayId')
def test_simulate_internet_unavailability():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/simulate_internet_unavailability_rollback.feature',
          'Simulate rollback after test execution')
def test_simulate_internet_unavailability_rollback():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
