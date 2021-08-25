# coding=utf-8

from pytest_bdd import (
    scenario
)


@scenario('../features/accidental_delete_usual_case.feature',
          'Execute Digito-AccidentalDeleteS3Objects_2020-04-01 to to accidentally delete files in S3 bucket')
def test_accidental_delete_usual_case():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@scenario('../features/accidental_delete_alarm_failed.feature',
          'Execute Digito-AccidentalDeleteS3Objects_2020-04-01 to accidentally delete files in S3 bucket '
          'and fail because of timed out alarm instead of being in ALARM state')
def test_accidental_delete_alarm_failed():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
