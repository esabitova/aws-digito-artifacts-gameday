
from pytest_bdd import scenario


@scenario('../features/service_task_failure_usual_case.feature',
          'Execute SSM automation document Digito-ServiceTaskFailure_2020-04-01')
def test_service_task_failure_usual_case():
    """Execute SSM automation document Digito-ServiceTaskFailure_2020-04-01"""
