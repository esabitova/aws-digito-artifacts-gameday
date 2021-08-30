# coding=utf-8
from pytest_bdd import (
    scenario
)


@scenario('../features/backup_number_of_backup_jobs_aborted.feature',
          'Attach NumberOfBackupJobsAborted alarm to Document and trigger it')
def test_backup_number_of_backup_jobs_aborted():
    pass
