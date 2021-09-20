
from pytest_bdd import scenario


@scenario('../features/reboot_db_instance_usual_case.feature',
          'Execute SSM automation document Digito-RebootDocumentDBInstanceTest_2020-09-21')
def test_reboot_db_instance_usual_case():
    """Execute SSM automation document Digito-RebootDocumentDBInstanceTest_2020-09-21"""
