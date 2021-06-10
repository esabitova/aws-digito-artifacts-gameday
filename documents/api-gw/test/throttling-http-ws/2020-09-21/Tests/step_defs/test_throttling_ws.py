
from pytest_bdd import scenario


@scenario('../features/throttling_ws_usual_case.feature',
          'Execute SSM automation document Digito-ThrottlingHttpWs_2020-09-21 for WS API')
def test_throttling_ws_usual_case():
    """Execute SSM automation document Digito-ThrottlingHttpWs_2020-09-21"""


@scenario('../features/throttling_ws_rollback_previous.feature',
          'Execute SSM automation document Digito-ThrottlingHttpWs_2020-09-21 for WS API in rollback')
def test_throttling_ws_rollback_previous():
    """Execute SSM automation document Digito-ThrottlingHttpWs_2020-09-21 in rollback"""


@scenario('../features/throttling_ws_failed.feature',
          'Execute SSM automation document Digito-ThrottlingHttpWs_2020-09-21 for WS API to test failure case')
def test_throttling_ws_failed():
    """Execute SSM automation document Digito-ThrottlingHttpWs_2020-09-21 to test failure case"""
