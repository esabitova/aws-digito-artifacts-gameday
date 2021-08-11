# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/redshift_num_exceeded_schema_quotas.feature',
          'Create redshift:alarm:num_exceeded_schema_quotas:2020-04-01 '
          'based on NumExceededSchemaQuotas metric and check OK status')
def test_redshift_num_exceeded_schema_quotas():
    pass
