# coding=utf-8

from pytest_bdd import scenario


% for scenario in scenarios:
@scenario('${scenario.feature_file}',
          '${scenario.name}')
def test_${get_test_suffix(scenario.feature_file)}():
    """${scenario.name}"""


% endfor