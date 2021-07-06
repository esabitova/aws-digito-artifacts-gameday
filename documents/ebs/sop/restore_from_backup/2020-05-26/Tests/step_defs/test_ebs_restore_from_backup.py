
from pytest_bdd import scenario


@scenario('../features/restore_from_backup_usual_case.feature',
          'Execute SSM automation document Digito-EBSRestoreFromBackup_2020-05-26')
def test_restore_from_backup():
    """Execute SSM automation document Digito-EBSRestoreFromBackup_2020-05-26"""
