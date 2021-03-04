# coding=utf-8
"""SSM automation document to reboot DB instance."""

from pytest_bdd import (
    scenario
)


@scenario('../features/reboot_db_instance.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document to reboot DB instance when the database doesn’t respond to any requests')
def test_reboot_db_instance():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""