
from pytest_bdd import scenario


@scenario('../features/scale_service_fargate_usual_case.feature',
          'Execute SSM automation document Digito-ScaleECSServiceSOP_2020-04-01 on Fargate. '
          'NewTaskDefinition. NumberOfTasks.')
def test_scale_service_fargate_usual_case_new_task_def_number_of_task():
    """Execute SSM automation document Digito-ScaleECSServiceSOP_2020-04-01"""


@scenario('../features/scale_service_fargate_usual_case.feature',
          'Execute SSM automation document Digito-ScaleECSServiceSOP_2020-04-01 on Fargate. '
          'NewTaskDefinition. No NumberOfTasks.')
def test_scale_service_fargate_usual_case_new_task_def_no_number_of_task():
    """Execute SSM automation document Digito-ScaleECSServiceSOP_2020-04-01"""


@scenario('../features/scale_service_fargate_usual_case.feature',
          'Execute SSM automation document Digito-ScaleECSServiceSOP_2020-04-01 on Fargate. '
          'No NewTaskDefinition. No NumberOfTasks.')
def test_scale_service_fargate_usual_case_no_new_task_def_no_number_of_task():
    """Execute SSM automation document Digito-ScaleECSServiceSOP_2020-04-01"""


@scenario('../features/scale_service_fargate_usual_case.feature',
          'Execute SSM automation document Digito-ScaleECSServiceSOP_2020-04-01 on Fargate. '
          'No NewTaskDefinition. NumberOfTasks.')
def test_scale_service_fargate_usual_no_case_new_task_def_number_of_task():
    """Execute SSM automation document Digito-ScaleECSServiceSOP_2020-04-01"""


@scenario('../features/scale_service_fargate_usual_case.feature',
          'Execute SSM automation document Digito-ScaleECSServiceSOP_2020-04-01 on Fargate. '
          'No NewTaskDefinition. Memory and CPU.')
def test_scale_service_fargate_usual_case_memory_cpu():
    """Execute SSM automation document Digito-ScaleECSServiceSOP_2020-04-01"""


@scenario('../features/scale_service_usual_case.feature',
          'Execute SSM automation document Digito-ScaleECSServiceSOP_2020-04-01 on EC2. '
          'NewTaskDefinition. NumberOfTasks.')
def test_scale_service_usual_case_new_task_def_number_of_task():
    """Execute SSM automation document Digito-ScaleECSServiceSOP_2020-04-01"""


@scenario('../features/scale_service_usual_case.feature',
          'Execute SSM automation document Digito-ScaleECSServiceSOP_2020-04-01 on EC2. '
          'NewTaskDefinition. No NumberOfTasks.')
def test_scale_service_usual_case_new_task_def_no_number_of_task():
    """Execute SSM automation document Digito-ScaleECSServiceSOP_2020-04-01"""


@scenario('../features/scale_service_usual_case.feature',
          'Execute SSM automation document Digito-ScaleECSServiceSOP_2020-04-01 on EC2. '
          'No NewTaskDefinition. No NumberOfTasks.')
def test_scale_service_usual_case_no_new_task_def_no_number_of_task():
    """Execute SSM automation document Digito-ScaleECSServiceSOP_2020-04-01"""


@scenario('../features/scale_service_usual_case.feature',
          'Execute SSM automation document Digito-ScaleECSServiceSOP_2020-04-01 on EC2. '
          'No NewTaskDefinition. NumberOfTasks.')
def test_scale_service_usual_no_case_new_task_def_number_of_task():
    """Execute SSM automation document Digito-ScaleECSServiceSOP_2020-04-01"""


@scenario('../features/scale_service_usual_case.feature',
          'Execute SSM automation document Digito-ScaleECSServiceSOP_2020-04-01 on EC2. '
          'No NewTaskDefinition. Memory and CPU.')
def test_scale_service_usual_case_memory_cpu():
    """Execute SSM automation document Digito-ScaleECSServiceSOP_2020-04-01"""
