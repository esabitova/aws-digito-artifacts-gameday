
from pytest_bdd import scenario


@scenario('../features/network_gw_lb_target_unavailable_usual_case.feature',
          'Create Network LB and execute automation to make the target group unavailable')
def test_network_lb_target_unavailable_usual_case():
    """Create Network LB and execute automation to make the target group unavailable"""


@scenario('../features/network_gw_lb_target_unavailable_usual_case.feature',
          'Create Network LB and execute automation to make the target group unavailable '
          'with target groups specified')
def test_network_lb_target_unavailable_usual_case_tg_specified():
    """Create Network LB and execute automation to make the target group unavailable  with target groups specified"""


@scenario('../features/network_gw_lb_target_unavailable_usual_case.feature',
          'Create Gateway LB and execute automation to make the target group unavailable')
def test_gateway_target_unavailable_usual_case():
    """Create Gateway LB and execute automation to make the target group unavailable"""


@scenario('../features/network_gw_lb_target_unavailable_usual_case.feature',
          'Create Gateway LB and execute automation to make the target group unavailable'
          ' with target groups specified')
def test_gateway_target_unavailable_usual_case_tg_specified():
    """Create Gateway LB and execute automation to make the target group unavailable"""


@scenario('../features/network_gw_lb_target_unavailable_rollback_previous.feature',
          'Create Network LB and execute automation to make the target group unavailable in rollback')
def test_network_lb_target_unavailable_rollback_previous():
    """Create Network LB and execute automation to make the target group unavailable in rollback"""


@scenario('../features/network_gw_lb_target_unavailable_rollback_previous.feature',
          'Create Gateway LB and execute automation to make the target group unavailable in rollback')
def test_gateway_lb_target_unavailable_rollback_previous():
    """Create Gateway LB and execute automation to make the target group unavailable in rollback"""


@scenario('../features/network_gw_lb_target_unavailable_failed.feature',
          'Create Network LB and execute automation to make the target group unavailable to test failure case')
def test_network_lb_target_unavailable_failed():
    """Create Network LB and execute automation to make the target group unavailable to test failure case"""


@scenario('../features/network_gw_lb_target_unavailable_failed.feature',
          'Create Gateway LB and execute automation to make the target group unavailable to test failure case')
def test_gateway_lb_target_unavailable_failed():
    """Create Gateway LB and execute automation to make the target group unavailable to test failure case"""
