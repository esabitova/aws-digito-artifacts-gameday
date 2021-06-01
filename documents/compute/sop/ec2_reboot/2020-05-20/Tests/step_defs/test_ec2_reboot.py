# coding=utf-8

from pytest_bdd import scenario


@scenario('../features/ec2_reboot_usual_case.feature',
          'Execute SSM automation document Digito-Ec2Reboot_2020-05-20')
def test_ec2_reboot_usual_case():
    """Execute SSM automation document Digito-Ec2Reboot_2020-05-20"""


