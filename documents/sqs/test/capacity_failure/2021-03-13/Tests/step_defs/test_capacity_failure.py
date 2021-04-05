# coding=utf-8

from pytest_bdd import (
    scenario
)


@scenario('../features/capacity_failure_standard_usual_case.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document')
def test_capacity_failure_standard_usual_case():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/capacity_failure_standard_failed.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document')
def test_capacity_failure_standard_failed():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/capacity_failure_standard_rollback_previous.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document')
def test_capacity_failure_standard_rollback_previous():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/capacity_failure_fifo_usual_case.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document')
def test_capacity_failure_fifo_usual_case():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/capacity_failure_fifo_failed.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document')
def test_capacity_failure_fifo_failed():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/capacity_failure_fifo_rollback_previous.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document')
def test_capacity_failure_fifo_rollback_previous():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
