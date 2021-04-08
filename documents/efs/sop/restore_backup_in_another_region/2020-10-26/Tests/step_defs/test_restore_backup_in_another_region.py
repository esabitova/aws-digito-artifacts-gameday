# coding=utf-8
"""SSM automation document to restore backup in another region"""

from pytest_bdd import (
    scenario,
)
import logging


logger = logging.getLogger(__name__)


@scenario('../features/restore_backup_in_another_region.feature',
          'Restore backup in another region')
def test_restore_backup():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
