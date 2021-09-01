from pytest_bdd import scenario


@scenario('../features/throttling_http_usual_case.feature',
          'Execute SSM automation document Digito-TriggerHttpWsApiGwThrottlingTest_2020-09-21 for HTTP API')
def test_throttling_http_usual_case():
    """Execute SSM automation document Digito-TriggerHttpWsApiGwThrottlingTest_2020-09-21"""


@scenario('../features/throttling_http_rollback_previous.feature',
          'Execute SSM automation document Digito-TriggerHttpWsApiGwThrottlingTest_2020-09-21 for HTTP API in rollback')
def test_throttling_http_rollback_previous():
    """Execute SSM automation document Digito-TriggerHttpWsApiGwThrottlingTest_2020-09-21 in rollback"""


@scenario('../features/throttling_http_failed.feature',
          'Execute SSM automation document Digito-TriggerHttpWsApiGwThrottlingTest_2020-09-21 for HTTP API to test '
          'failure case')
def test_throttling_http_failed():
    """Execute SSM automation document Digito-TriggerHttpWsApiGwThrottlingTest_2020-09-21 to test failure case"""
