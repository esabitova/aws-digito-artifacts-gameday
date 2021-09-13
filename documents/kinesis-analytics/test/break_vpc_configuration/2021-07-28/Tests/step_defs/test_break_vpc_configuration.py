
from pytest_bdd import scenario


@scenario('../features/break_vpc_configuration_usual_case.feature',
          'Execute SSM automation document Digito-BreakKinesisDataAnalyticsVpcConfigurationTest_2021-07-28')
def test_break_vpc_configuration_usual_case():
    """Execute SSM automation document Digito-BreakKinesisDataAnalyticsVpcConfigurationTest_2021-07-28"""


@scenario('../features/break_vpc_configuration_rollback_previous.feature',
          'Execute SSM automation document Digito-BreakKinesisDataAnalyticsVpcConfigurationTest_2021-07-28 '
          'in rollback')
def test_break_vpc_configuration_rollback_previous():
    """
    Execute SSM automation document Digito-BreakKinesisDataAnalyticsVpcConfigurationTest_2021-07-28
    in rollback
    """


@scenario('../features/break_vpc_configuration_failed.feature',
          'Execute SSM automation document Digito-BreakKinesisDataAnalyticsVpcConfigurationTest_2021-07-28 '
          'to test failure case')
def test_break_vpc_configuration_failed():
    """
    Execute SSM automation document Digito-Digito-BreakKinesisDataAnalyticsVpcConfigurationTest_2021-07-28
    to test failure case
    """
