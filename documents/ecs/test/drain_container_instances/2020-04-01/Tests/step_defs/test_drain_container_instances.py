
from pytest_bdd import scenario


@scenario('../features/drain_container_instances_usual_case.feature',
          'Execute SSM automation document Digito-DrainContainerInstances_2020-04-01')
def test_drain_container_instances_usual_case():
    """Execute SSM automation document Digito-DrainContainerInstances_2020-04-01"""
