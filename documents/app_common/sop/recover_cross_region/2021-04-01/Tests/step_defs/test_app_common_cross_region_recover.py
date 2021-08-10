
from pytest_bdd import scenario


@scenario('../features/app_common_recover_cross_region.feature',
          'Execute SSM automation document Digito-AppCommonRecoverCrossRegion_2021-04-01')
def test_app_common_cross_region_recover():
    """Execute SSM automation document Digito-AppCommonRecoverCrossRegion_2021-04-01"""
