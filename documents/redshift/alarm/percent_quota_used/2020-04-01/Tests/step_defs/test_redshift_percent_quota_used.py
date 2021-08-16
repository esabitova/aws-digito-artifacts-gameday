# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/redshift_percent_quota_used.feature',
          'Create redshift:alarm:percent_quota_used:2020-04-01 based on '
          'PercentageQuotaUsed metric and check OK status')
def test_redshift_percent_quota_used():
    pass
