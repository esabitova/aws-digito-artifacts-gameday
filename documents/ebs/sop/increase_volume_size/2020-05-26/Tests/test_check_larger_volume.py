import unittest
import pytest

from documents.ebs.sop.increase_volume_size.python.check_larger_volume import CheckLargerVolume


@pytest.mark.unit_test
class TestCheckLargerVolume(unittest.TestCase):

    def test_check_larger_volume_smaller(self):
        python_step = CheckLargerVolume()
        params = {'DescribeInstanceVolume.CurrentSizeGiB': 4, 'SizeGib': 5}
        python_step.invoke(params)
        self.assertFalse(params['CheckLargerVolume.VolumeAlreadyGreater'])

    def test_check_larger_volume_greater(self):
        python_step = CheckLargerVolume()
        params = {'DescribeInstanceVolume.CurrentSizeGiB': 4, 'SizeGib': 3}
        python_step.invoke(params)
        self.assertTrue(params['CheckLargerVolume.VolumeAlreadyGreater'])

    def test_check_larger_volume_same(self):
        python_step = CheckLargerVolume()
        params = {'DescribeInstanceVolume.CurrentSizeGiB': 4, 'SizeGib': 4}
        python_step.invoke(params)
        self.assertTrue(params['CheckLargerVolume.VolumeAlreadyGreater'])
