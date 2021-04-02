# coding=utf-8
"""SSM automation document for Aurora backtrack."""
from pytest_bdd import (
    scenario,
    parsers,
    given
)
import datetime


@scenario('../features/backtrack.feature', 'Create AWS resources using CloudFormation template '
          'and execute SSM automation document to backtrack')
def test_backtrack():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""


@given(parsers.parse('cache backtrack time "{backtrack_time}"'))
def cache_backtrack_time(ssm_test_cache):
    ssm_test_cache['backtrack_time'] = datetime.datetime.now().isoformat()
