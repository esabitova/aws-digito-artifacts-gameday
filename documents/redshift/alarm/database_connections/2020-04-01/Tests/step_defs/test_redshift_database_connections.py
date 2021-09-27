# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/redshift_database_connections.feature',
          'Create redshift:alarm:database_connections:2020-04-01 based on '
          'DatabaseConnections metric and check that datapoints exist.')
def test_redshift_database_connections():
    pass
