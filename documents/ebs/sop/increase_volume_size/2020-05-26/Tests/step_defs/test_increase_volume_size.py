
from pytest_bdd import scenario


@scenario('../features/increase_volume_size.feature',
          'Execute SSM automation document Digito-EBSIncreaseVolumeSize_2020-05-26')
def test_increase_volume_size():
    """Execute SSM automation document Digito-EBSIncreaseVolumeSize_2020-05-26"""
