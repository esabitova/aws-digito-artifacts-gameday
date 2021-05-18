from pytest_bdd import (
    scenario
)


@scenario('../features/break_security_group.feature',
          'Create AWS resources using CloudFormation template and execute SSM automation document to '
          'test EFS behavior after breaking security group id')
def test_break_security_group():
    """Create AWS resources using CloudFormation template and execute SSM automation document."""
