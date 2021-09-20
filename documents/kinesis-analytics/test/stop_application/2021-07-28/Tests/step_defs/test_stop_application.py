
from pytest_bdd import scenario


@scenario('../features/stop_application_usual_case.feature',
          'Execute SSM automation document Digito-StopKinesisDataAnalyticsApplicationTest_2021-07-28')
def test_stop_application_usual_case():
    """Execute SSM automation document Digito-StopKinesisDataAnalyticsApplicationTest_2021-07-28"""


@scenario('../features/stop_application_rollback_previous.feature',
          'Execute SSM automation document Digito-StopKinesisDataAnalyticsApplicationTest_2021-07-28 '
          'in rollback test')
def test_stop_application_rollback_previous():
    """
    Execute SSM automation document Digito-StopKinesisDataAnalyticsApplicationTest_2021-07-28
    in rollback
    """


@scenario('../features/stop_application_failed.feature',
          'Execute SSM automation document Digito-StopKinesisDataAnalyticsApplicationTest_2021-07-28 '
          'to test failure case')
def test_stop_application_failed():
    """
    Execute SSM automation document Digito-StopKinesisDataAnalyticsApplicationTest_2021-07-28
    to test failure case
    """
