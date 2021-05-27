from pytest_bdd import scenario


@scenario('../features/throttling_rest_usual_case.feature',
          'Execute SSM automation document Digito-RestApiGwThrottling_2020-09-21 without stage name provided')
def test_throttling_rest_usual_case():
    """Execute SSM automation document Digito-ThrottlingRest_2020-09-21"""


@scenario('../features/throttling_rest_usual_case.feature',
          'Execute SSM automation document Digito-RestApiGwThrottling_2020-09-21 with stage name provided')
def test_throttling_rest_usual_case_with_stage_name():
    """Execute SSM automation document Digito-ThrottlingRest_2020-09-21"""


@scenario('../features/throttling_rest_rollback_previous.feature',
          'Execute SSM automation document Digito-RestApiGwThrottling_2020-09-21 in rollback'
          ' without stage name provided')
def test_throttling_rest_rollback_case():
    """Execute SSM automation document Digito-ThrottlingRest_2020-09-21"""


@scenario('../features/throttling_rest_rollback_previous.feature',
          'Execute SSM automation document Digito-RestApiGwThrottling_2020-09-21 in rollback'
          ' with stage name provided')
def test_throttling_rest_rollback_case_with_stage_name():
    """Execute SSM automation document Digito-ThrottlingRest_2020-09-21"""


@scenario('../features/throttling_rest_rollback_negative.feature',
          'Execute SSM automation document Digito-RestApiGwThrottling_2020-09-21 in negative rollback'
          ' test with wrong Usage Plan ID')
def test_throttling_rest_negative_rollback_case_with_wrong_usage_plan_id():
    """Execute SSM automation document Digito-ThrottlingRest_2020-09-21"""


@scenario('../features/throttling_rest_rollback_negative.feature',
          'Execute SSM automation document Digito-RestApiGwThrottling_2020-09-21 in negative rollback'
          ' test with wrong Stage Name')
def test_throttling_rest_negative_rollback_case_with_wrong_stage_name():
    """Execute SSM automation document Digito-ThrottlingRest_2020-09-21"""


@scenario('../features/throttling_rest_rollback_negative.feature',
          'Execute SSM automation document Digito-RestApiGwThrottling_2020-09-21 in negative rollback'
          ' test with wrong API Gateway ID')
def test_throttling_rest_negative_rollback_case_with_wrong_api_gateway_id():
    """Execute SSM automation document Digito-ThrottlingRest_2020-09-21"""


@scenario('../features/throttling_rest_failed.feature',
          'Execute SSM automation document Digito-RestApiGwThrottling_2020-09-21 in failed'
          ' test without Stage Name')
def test_throttling_rest_failed_case():
    """Execute SSM automation document Digito-ThrottlingRest_2020-09-21"""


@scenario('../features/throttling_rest_failed.feature',
          'Execute SSM automation document Digito-RestApiGwThrottling_2020-09-21 in failed'
          ' test with Stage Name')
def test_throttling_rest_failed_case_with_stage_name():
    """Execute SSM automation document Digito-ThrottlingRest_2020-09-21"""
