# coding=utf-8
"""SSM automation document to increase Lambda memory size"""
from pytest_bdd import (
    scenario
)


@scenario('../features/change_concurrency_limit.feature', 'Change Concurrency limit of Lambda Function')
def test_change_concurrency_limit():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/change_concurrency_limit.feature', 'Set Concurrency limit out of account limits')
def test_concurrency_limit_out_of_quota():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
