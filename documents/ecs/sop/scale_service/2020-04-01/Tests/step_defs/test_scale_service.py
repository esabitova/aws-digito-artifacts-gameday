from pytest_bdd import scenario


@scenario('../features/scale_service_usual_case.feature',
          'Execute SSM automation document Digito-ScaleService_2020-04-01 on EC2'
          ' to apply new task definition to service')
def test_scale_service_usual_case():
    """Execute SSM automation document Digito-ScaleService_2020-04-01"""


# @scenario('../features/scale_service_fargate_usual_case.feature',
#           'Execute SSM automation document Digito-ScaleService_2020-04-01 on Fargate'
#           ' to apply new task definition to service')
# def test_scale_service_fargate_usual_case():
#     """Execute SSM automation document Digito-ScaleService_2020-04-01"""
