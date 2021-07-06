
from pytest_bdd import scenario


@scenario('../features/scale_service_usual_case.feature',
          'Execute SSM automation document Digito-ScaleService_2020-04-01')
def test_scale_service_usual_case():
    """Execute SSM automation document Digito-ScaleService_2020-04-01"""
