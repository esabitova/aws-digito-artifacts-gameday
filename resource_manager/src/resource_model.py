import logging
from pynamodb.indexes import AllProjection
from pynamodb.models import Model
from pynamodb.attributes import (
    UnicodeAttribute,
    JSONAttribute,
    UTCDateTimeAttribute,
    NumberAttribute,
    VersionAttribute)
from datetime import datetime
from enum import Enum


class ResourceModel(Model):
    """
    Pynamo DB model for CloudFormation created resources outputs.
    """

    @staticmethod
    def configure(boto3_session):
        ResourceModel.Meta.region = boto3_session.region_name

    class Meta:
        table_name = 'ssm-test-resources'
        # All attributes are projected
        projection = AllProjection()

    class Status(Enum):
        """
        Enumeration for resource availability status
        """
        AVAILABLE = 1,
        LEASED = 2,
        CREATING = 3,
        UPDATING = 4,
        DELETING = 5,
        DELETED = 6,
        DELETE_FAILED = 7,
        EXECUTE_FAILED = 8,
        CREATE_FAILED = 9,
        UPDATE_FAILED = 10

        @staticmethod
        def from_string(resource_status):
            for rs in ResourceModel.Status:
                if rs.name == resource_status:
                    return rs
            raise Exception(f'Resource status for name [{resource_status}] is not supported.')

    class Type(Enum):
        DEDICATED = 1,
        ON_DEMAND = 2,
        ASSUME_ROLE = 3,
        SHARED = 4

        @staticmethod
        def from_string(resource_type):
            for rt in ResourceModel.Type:
                if rt.name == resource_type:
                    return rt
            raise Exception(f'Resource type for name [{resource_type}] is not supported.')

    cf_template_name = UnicodeAttribute(hash_key=True)
    cf_stack_name = UnicodeAttribute(range_key=True)
    cfn_dependency_stacks = JSONAttribute(null=True)
    last_execution = UnicodeAttribute(null=True)
    pool_size = NumberAttribute()
    status = UnicodeAttribute()
    type = UnicodeAttribute()
    cf_template_url = UnicodeAttribute(null=True)
    cf_template_sha1 = UnicodeAttribute(null=True)
    test_session_id = UnicodeAttribute()
    cf_input_parameters = JSONAttribute(null=True)
    cf_input_parameters_sha1 = UnicodeAttribute(null=True)
    cf_output_parameters = JSONAttribute(null=True)
    leased_on = UTCDateTimeAttribute()
    created_on = UTCDateTimeAttribute()
    updated_on = UTCDateTimeAttribute()
    leased_times = NumberAttribute(default=0)
    cf_stack_index = NumberAttribute()
    version = VersionAttribute()

    @staticmethod
    def create_ddb_table():
        """
        Creates DDB table for cloud formation stack resources which is used by resource manager.
        """
        if ResourceModel().exists():
            logging.info("Table for name [%s] already exist.", ResourceModel.Meta.table_name)
        else:
            ResourceModel().create_table(billing_mode="PAY_PER_REQUEST", wait=True)
            logging.info("Table for name [%s] created.", ResourceModel.Meta.table_name)

    @staticmethod
    def get_resources_by_status(status) -> []:
        """
        Returns resource records based on given status.
        :param status: The status of resource record
        :return: List of resource records
        """
        resources = []
        for resource in ResourceModel.scan():
            if resource.status == status.name:
                resources.append(resource)
        return resources

    @staticmethod
    def update_status(resource, status: Status):
        """
        Updates resource record to given status.
        :param resource: The resource record to be updated
        :param status: The resource status
        """
        resource.updated_on = datetime.now()
        resource.status = status.name
        resource.save()

    @staticmethod
    def query_by_template(cfn_template_path: str) -> []:
        """
        Returns resources by template name path.
        :param cfn_template_path: The cloud formation template path.
        :return: The list of resources.
        """
        resources = []
        for r in ResourceModel.query(cfn_template_path):
            resources.append(r)
        return resources

    @staticmethod
    def create(**kwargs):
        record = ResourceModel(**kwargs)
        record.save()
        return record
