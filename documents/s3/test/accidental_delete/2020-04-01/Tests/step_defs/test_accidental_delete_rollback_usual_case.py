# coding=utf-8

from pytest_bdd import (
    scenario
)


@scenario('../features/accidental_delete_usual_case.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document to accidentally '
          'delete files in S3 bucket')
def test_accidental_delete_usual_case():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
