# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/backup_number_of_restore_jobs_failed.feature',
          'Attach NumberOfRestoreJobsFailed alarm to Document and trigger it')
def test_backup_number_of_restore_jobs_failed():
    pass
