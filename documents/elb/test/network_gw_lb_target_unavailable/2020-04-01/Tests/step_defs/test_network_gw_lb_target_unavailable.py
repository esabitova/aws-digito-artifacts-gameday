
from pytest_bdd import scenario


@scenario('../features/network_gw_lb_target_unavailable_usual_case.feature',
          'Create Network LB and execute automation')
def test_network_lb_target_unavailable_usual_case():
    """Create Network LB and execute automation"""


@scenario('../features/network_gw_lb_target_unavailable_usual_case.feature',
          'Create Network LB and execute automation')
def test_gateway_target_unavailable_usual_case():
    """Create Gateway LB and execute automation"""


@scenario('../features/network_gw_lb_target_unavailable_rollback_previous.feature',
          'Create Network LB and execute automation in rollback')
def test_network_lb_target_unavailable_rollback_previous():
    """Create Network LB and execute automation in rollback"""


@scenario('../features/network_gw_lb_target_unavailable_rollback_previous.feature',
          'Create Network LB and execute automation in rollback')
def test_gateway_lb_target_unavailable_rollback_previous():
    """Create Gateway LB and execute automation in rollback"""


@scenario('../features/network_gw_lb_target_unavailable_failed.feature',
          'Create Network LB and execute automation to test failure case')
def test_network_lb_target_unavailable_failed():
    """Create Network LB and execute automation to test failure case"""


@scenario('../features/network_gw_lb_target_unavailable_failed.feature',
          'Create Network LB and execute automation to test failure case')
def test_gateway_lb_target_unavailable_failed():
    """Create Gateway LB and execute automation to test failure case"""
