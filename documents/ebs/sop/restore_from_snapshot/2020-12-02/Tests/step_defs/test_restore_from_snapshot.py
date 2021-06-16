
from pytest_bdd import scenario


@scenario('../features/restore_from_snapshot_usual_case.feature',
          'Execute SSM automation document Digito-EBSRestoreFromSnapshot_2020-12-02')
def test_restore_from_snapshot_usual_case():
    """Execute SSM automation document Digito-EBSRestoreFromSnapshot_2020-12-02"""
