
from pytest_bdd import scenario


@scenario('../features/change_throttling_settings_http_without_overwrite.feature',
          'Change throttling settings for HTTP API Gateway with ForceExecution=False and without provided route key')
def test_change_throttling_settings_http_without_overwrite():
    """Execute SSM automation document Digito-ChangeThrottlingSettingsHttpWs_2020-10-26"""


@scenario('../features/change_throttling_settings_http_without_overwrite.feature',
          'Change throttling settings for HTTP API Gateway with ForceExecution=False and with the specified route key')
def test_change_throttling_settings_http_without_overwrite_route():
    """Execute SSM automation document Digito-ChangeThrottlingSettingsHttpWs_2020-10-26"""
