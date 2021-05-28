from pytest_bdd import scenario


@scenario('../features/rest_api_quota_usual_case.feature',
          'Execute SSM automation document Digito-RestApiGwQuota_2020-09-21')
def test_rest_api_quota_usual_case():
    """Execute SSM automation document Digito-RestApiGwQuota_2020-09-21"""


@scenario('../features/rest_api_quota_failed.feature',
          'Execute SSM automation document Digito-RestApiGwQuota_2020-09-21 in failed test')
def test_rest_api_quota_failed_case():
    """Execute SSM automation document Digito-RestApiGwQuota_2020-09-21"""


@scenario('../features/rest_api_quota_rollback_previous.feature',
          'Execute SSM automation document Digito-RestApiGwQuota_2020-09-21 in rollback test')
def test_rest_api_quota_rollback_case():
    """Execute SSM automation document Digito-RestApiGwQuota_2020-09-21"""


@scenario('../features/rest_api_quota_rollback_negative.feature',
          'Execute SSM automation document Digito-RestApiGwQuota_2020-09-21 in negative rollback test')
def test_rest_api_quota_negative_rollback_case():
    """Execute SSM automation document Digito-RestApiGwQuota_2020-09-21"""
