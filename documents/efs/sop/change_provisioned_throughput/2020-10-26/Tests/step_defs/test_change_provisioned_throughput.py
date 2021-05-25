
from pytest_bdd import scenario


@scenario('../features/change_provisioned_throughput_usual_case.feature',
          'Execute SSM automation document Digito-EFSChangeProvisionedThroughput_2020-10-26')
def test_change_provisioned_throughput_usual_case():
    """Execute SSM automation document Digito-EFSChangeProvisionedThroughput_2020-10-26"""
