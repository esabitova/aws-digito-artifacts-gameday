
from pytest_bdd import scenario


@scenario('../features/scaling_up_usual_case.feature',
          'Execute SSM automation document Digito-ScaleUpDocumentDBClusterSOP_2020-09-21')
def test_scaling_up_usual_case():
    """Execute SSM automation document Digito-ScaleUpDocumentDBClusterSOP_2020-09-21"""
