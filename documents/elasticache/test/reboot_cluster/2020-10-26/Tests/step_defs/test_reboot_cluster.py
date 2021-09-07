
from pytest_bdd import scenario


@scenario('../features/reboot_cluster_usual_case.feature',
          'Execute SSM automation document Digito-RebootElasticacheClusterTest_2020-10-26')
def test_reboot_cluster_usual_case():
    """Execute SSM automation document Digito-RebootElasticacheClusterTest_2020-10-26"""
