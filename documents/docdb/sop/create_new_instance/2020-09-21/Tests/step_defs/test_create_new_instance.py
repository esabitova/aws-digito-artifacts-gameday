# coding=utf-8
"""SSM automation document to create a new DB instance."""

from pytest_bdd import (
    scenario
)


@scenario('../features/create_new_instance.feature',
          'Create a new instance in a specified AZ/Region')
def test_create_new_instance():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/create_new_instance.feature',
          'Create a new instance without specifying AZ')
def test_create_new_instance_without_specifying_az():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
