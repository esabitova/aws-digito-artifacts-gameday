from datetime import datetime, timezone, timedelta

AUTOMATION_EXECUTION_ID = '123e4567-e89b-12d3-a456-426614174000'
STEP_NAME = 'StepName'
MISSING_STEP_NAME = 'MissingStepName'
INSTANCE_ID = 'i-12345'
SUCCESS_STATUS = 'Success'
RESPONSE_FIELD_1 = 'Status'
RESPONSE_FIELD_2 = 'InstanceId'
APPLICATION_SUBNET_ID = 'subnet-12345'
ROUTE_TABLE_ID = 'rtb-12345'
NAT_GATEWAY_ID = 'nat-12345'
IGW_ID = 'igw-12345'
INTERNET_DESTINATION = '0.0.0.0/0'
STEP_DURATION = 8
EXECUTION_START_TIME = datetime.now(timezone.utc) - timedelta(seconds=STEP_DURATION)
EXECUTION_END_TIME = datetime.now(timezone.utc)
DB_INSTANCE_ID = 'db'
TARGET_DB_INSTANCE_ID = 'db-new'
RECOVERY_POINT = 300

def get_sample_ssm_execution_response():
    step_execution_outputs = {}
    step_execution_outputs[RESPONSE_FIELD_1] = [SUCCESS_STATUS]
    step_execution_outputs[RESPONSE_FIELD_2] = [INSTANCE_ID]

    step_execution = {}
    step_execution['Outputs'] = step_execution_outputs
    step_execution['StepName'] = STEP_NAME
    step_execution['ExecutionStartTime'] = EXECUTION_START_TIME
    step_execution['ExecutionEndTime'] = EXECUTION_END_TIME

    automation_execution = {}
    automation_execution['StepExecutions'] = [step_execution]
    automation_execution['AutomationExecutionId'] = AUTOMATION_EXECUTION_ID

    ssm_execution_response = {}
    ssm_execution_response['AutomationExecution'] = automation_execution

    return ssm_execution_response

def get_sample_route_table_response():
    route_1 = {}
    route_1['DestinationCidrBlock'] = '10.0.0.0/16'
    route_1['GatewayId'] = 'local'
    route_1['Origin'] = 'CreateRouteTable'
    route_1['State'] = 'active'

    route_natgw = {}
    route_natgw['DestinationCidrBlock'] = INTERNET_DESTINATION
    route_natgw['NatGatewayId'] = NAT_GATEWAY_ID
    route_natgw['Origin'] = 'CreateRoute'
    route_natgw['State'] = 'active'

    route_igw = {}
    route_igw['DestinationCidrBlock'] = INTERNET_DESTINATION
    route_igw['GatewayId'] = IGW_ID
    route_igw['Origin'] = 'CreateRoute'
    route_igw['State'] = 'active'

    route_table_1 = {}
    route_table_1['RouteTableId'] = ROUTE_TABLE_ID
    route_table_1['Routes'] = [route_1, route_natgw]

    route_table_2 = {}
    route_table_2['RouteTableId'] = ROUTE_TABLE_ID
    route_table_2['Routes'] = [route_1, route_igw]

    route_table_response = {}
    route_table_response['RouteTables'] = [route_table_1, route_table_2]

    return route_table_response

def get_sample_describe_db_instances_response():
    db_instances_response = {}

    vpc_security_group = {}
    vpc_security_group['VpcSecurityGroupId'] = 'sg-12345'

    db_subnet_group = {}
    db_subnet_group['DBSubnetGroupName'] = 'db-subnet-group'

    db_instance = {}
    db_instance['LatestRestorableTime'] = datetime.now(timezone.utc) - timedelta(seconds=RECOVERY_POINT)
    db_instance['MultiAZ'] = True
    db_instance['PubliclyAccessible'] = True
    db_instance['CopyTagsToSnapshot'] = True
    db_instance['VpcSecurityGroups'] = [vpc_security_group]
    db_instance['DBSubnetGroup'] = db_subnet_group

    db_instances_response['DBInstances'] = [db_instance]

    return db_instances_response