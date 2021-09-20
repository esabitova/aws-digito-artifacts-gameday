
from pytest_bdd import scenario


@scenario('../features/scaling_down_usual_case.feature',
          'Execute SSM automation document Digito-ScaleDownDocumentDBClusterSOP_2020-09-21')
def test_scaling_down_usual_case():
    """Execute SSM automation document Digito-ScaleDownDocumentDBClusterSOP_2020-09-21"""
