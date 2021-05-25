from pytest_bdd import scenario


@scenario('../features/throttling_rest_usual_case.feature',
          'Execute SSM automation document Digito-RestApiGwThrottling_2020-09-21 without stage name provided')
def test_throttling_rest_usual_case():
    """Execute SSM automation document Digito-ThrottlingRest_2020-09-21"""


@scenario('../features/throttling_rest_usual_case.feature',
          'Execute SSM automation document Digito-RestApiGwThrottling_2020-09-21 with stage name provided')
def test_throttling_rest_usual_case_with_stage_name():
    """Execute SSM automation document Digito-ThrottlingRest_2020-09-21"""
