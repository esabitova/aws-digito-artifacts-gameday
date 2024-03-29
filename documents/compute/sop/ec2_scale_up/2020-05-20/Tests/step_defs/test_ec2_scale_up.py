# coding=utf-8
import pytest
from pytest_bdd import scenario


@pytest.mark.skip(reason="Broken test: https://issues.amazon.com/issues/Digito-3229")
@scenario('../features/ec2_scale_up_usual_case.feature',
          'Execute SSM automation document Digito-Ec2ScaleUp_2020-05-20 and '
          'without instance type override')
def test_ec2_scale_up_usual_case():
    """Execute SSM automation document Digito-Ec2ScaleUp_2020-05-20"""


@scenario('../features/ec2_scale_up_usual_case.feature',
          'Execute SSM automation document Digito-Ec2ScaleUp_2020-05-20 and '
          'with instance type override')
def test_ec2_scale_up_override_type_case():
    """Execute SSM automation document Digito-Ec2ScaleUp_2020-05-20 with instance type override"""
