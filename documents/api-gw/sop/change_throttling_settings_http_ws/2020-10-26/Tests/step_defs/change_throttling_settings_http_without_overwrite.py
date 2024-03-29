
from pytest_bdd import scenario

# Success executions


@scenario('../features/change_throttling_settings_http_without_overwrite.feature',
          'Change throttling settings for HTTP API Gateway with no throttling, ForceExecution=False and with '
          'the specified route key')
def test_change_throttling_settings_http_without_overwrite_not_throttled():
    """Execute SSM automation document Digito-ChangeHttpWsApiGwThrottlingSettingsSOP_2020-10-26"""


@scenario('../features/change_throttling_settings_http_without_overwrite.feature',
          'Change throttling settings for HTTP API Gateway with throttling enabled, ForceExecution=False and with '
          'the specified route key')
def test_change_throttling_settings_http_without_overwrite_throttled():
    """Execute SSM automation document Digito-ChangeHttpWsApiGwThrottlingSettingsSOP_2020-10-26"""


# Failed executions (new values above 50%)


@scenario('../features/change_throttling_settings_http_without_overwrite.feature',
          'Fail to change rate limit above 50% for HTTP API Gateway with throttling enabled, ForceExecution=False and '
          'with the specified route key')
def test_change_throttling_settings_http_without_overwrite_throttled_rate_above_50():
    """Execute SSM automation document Digito-ChangeHttpWsApiGwThrottlingSettingsSOP_2020-10-26"""


@scenario('../features/change_throttling_settings_http_without_overwrite.feature',
          'Fail to change burst limit above 50% for HTTP API Gateway with throttling enabled, ForceExecution=False and '
          'with the specified route key')
def test_change_throttling_settings_http_without_overwrite_throttled_burst_above_50():
    """Execute SSM automation document Digito-ChangeHttpWsApiGwThrottlingSettingsSOP_2020-10-26"""


# Failed executions (new values above account quota)


@scenario('../features/change_throttling_settings_http_without_overwrite.feature',
          'Fail to change rate limit above account quota for HTTP API Gateway with throttling enabled, '
          'ForceExecution=False and with the specified route key')
def test_change_throttling_settings_http_without_overwrite_throttled_rate_above_account_quota():
    """Execute SSM automation document Digito-ChangeHttpWsApiGwThrottlingSettingsSOP_2020-10-26"""


@scenario('../features/change_throttling_settings_http_without_overwrite.feature',
          'Fail to change burst limit above account quota for HTTP API Gateway with throttling enabled, '
          'ForceExecution=False and with the specified route key')
def test_change_throttling_settings_http_without_overwrite_throttled_burst_above_account_quota():
    """Execute SSM automation document Digito-ChangeHttpWsApiGwThrottlingSettingsSOP_2020-10-26"""
