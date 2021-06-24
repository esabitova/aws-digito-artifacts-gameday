import boto3
import getopt
import logging
import sys
import os
import time
from enum import Enum
from botocore.exceptions import ClientError
from resource_manager.src.resource_model import ResourceModel
from concurrent.futures import ThreadPoolExecutor
from resource_manager.src.constants import s3_bucket_name_pattern, BgColors

logger = logging.getLogger('resource_tool')
logging.basicConfig(format='%(asctime)s %(name)s %(levelname)s:%(message)s', level=logging.INFO,
                    handlers=[logging.StreamHandler(sys.stdout)])


class Command(Enum):
    DESTROY = 0,
    LIST = 1,
    DESTROY_ALL = 2

    @staticmethod
    def from_string(command):
        for c in Command:
            if c.name == command:
                return c
        raise Exception('Command for name [{}] is not supported.'.format(command))


class ResourceTool:
    def __init__(self, boto3_session: boto3.Session):
        ResourceModel.configure(boto3_session)
        self.cfn_client = boto3_session.client('cloudformation')
        self.s3_resource = boto3_session.resource('s3')
        self.account_id = boto3_session.client('sts').get_caller_identity().get('Account')
        self.region = boto3_session.region_name

    def list_resources(self):
        """
        Lists and prints existing template names with associated cfn stack names.
        :return:
        """
        existing_template_names = {}
        for resource in ResourceModel.scan():
            cfn_file_name = self._get_cfn_template_file_name(resource.cf_template_name)
            if not existing_template_names.get(cfn_file_name):
                existing_template_names[cfn_file_name] = []
            dependencies = f', dependencies: {",".join(resource.cfn_dependency_stacks)}' \
                if resource.cfn_dependency_stacks else ''
            existing_template_names.get(cfn_file_name).append(f'[{resource.cf_stack_name}:{resource.status}'
                                                              f'{dependencies}]')
        for key in existing_template_names:
            print(BgColors.OKBLUE + f'* {key} -> {",".join(existing_template_names[key])}' + BgColors.ENDC)

    def destroy_resources(self, cfn_template_names: [] = None):
        """
        Destroys cloud formation stacks, deletes cfn template files from S3 and record from DDB based
        on list of given cfn template names.
        :param cfn_template_names: The list of cfn template names
        :return:
        """
        resources_to_delete = []
        stacks_to_delete = {}
        all_resources = self._get_all_resources()
        for resource in all_resources:
            cfn_file_name = self._get_cfn_template_file_name(resource.cf_template_name)
            # In case if cfn template list is given collect only template name related resources
            if cfn_template_names:
                if cfn_file_name in cfn_template_names:
                    dependents = self._find_resource_dependents(resource, all_resources)
                    if len(dependents) > 0 and \
                            not self._is_dependent_template_listed(cfn_template_names, dependents.keys()):
                        raise Exception(BgColors.FAIL + f'Stack for [{resource.cf_stack_name}] cannot be deleted due '
                                                        f'to following stacks are dependent: '
                                                        f'{list(dependents.values())}. Please delete dependend stacks '
                                                        f'first or list dependend stacks cfn templates together. '
                                                        f'For example if TemplateB stack depends on TemplateA '
                                                        f'stack: -t TemplateB,TemplateA.' + BgColors.ENDC)
                    resources_to_delete.append(resource)
                    if not stacks_to_delete.get(resource.cf_template_name):
                        stacks_to_delete[resource.cf_template_name] = []
                    stacks_to_delete.get(resource.cf_template_name).append(resource.cf_stack_name)
            # In case if cfn template list is NOT given collect all resources
            else:
                resources_to_delete.append(resource)
                if not stacks_to_delete.get(resource.cf_template_name):
                    stacks_to_delete[resource.cf_template_name] = []
                stacks_to_delete.get(resource.cf_template_name).append(resource.cf_stack_name)

        resource_count = len(resources_to_delete)
        if resource_count > 0:
            stack_names = self.dict_array_values_as_list(stacks_to_delete)
            logger.info(f" Destroying [{resource_count}] cloud formation stacks {stack_names}")
            with ThreadPoolExecutor(max_workers=10) as t_executor:
                for index in range(resource_count):
                    resource = resources_to_delete[index]
                    t_executor.submit(ResourceTool._delete_resource, self.cfn_client, resource, all_resources, logger)

            s3_bucket_name = self.get_s3_bucket_name(self.account_id, self.region)
            failed_resources = []
            for resource in ResourceModel.scan():
                if resource.status == ResourceModel.Status.DELETE_FAILED.name:
                    logger.error(f'Deleting [{resource.cf_stack_name}] stack failed.')
                    failed_resources.append(resource)
                if len(failed_resources) > 0:
                    err_message = f'Failed to delete [{ResourceModel.Meta.table_name}] DDB table and [{s3_bucket_name}] ' \
                                  f'S3 bucket due CFN stack deletion failure. For investigation purpose we do not ' \
                                  f'delete DDB table and S3 bucket ' \
                                  f'(feel free to delete DDB table/S3 bucket manually when ready). '
                    logger.error(err_message)
                    raise Exception(err_message)
            self._delete_s3_files(s3_bucket_name, stacks_to_delete)
        else:
            logger.warning(BgColors.WARNING + f" Nothing to destroy due to NO resources for template names "
                                              f"{cfn_template_names} found." + BgColors.ENDC)

    def _get_all_resources(self):
        """
        Lists all existing resouurces and created list as an output so that we can iterate it over.
        :return: The list of resources.
        """
        all_resources = []
        for resource in ResourceModel.scan():
            all_resources.append(resource)
        return all_resources

    def _is_dependent_template_listed(self, cfn_template_names: [], dependent_template_names: []) -> bool:
        """
        Returns true in case if dependent template is listed in command line.
        :param cfn_template_names: The list of cfn template names passed over CLI.
        :param dependent_template_names: The
        :return:
        """
        for dependent_template in dependent_template_names:
            if dependent_template not in cfn_template_names:
                return False
        return True

    def dict_array_values_as_list(self, dict_object: dict()) -> []:
        """
        Combines lists of cfn stacks mapped to cfn template in dict into single list of cfn stacks.
        :param dict_object: The lists of cfn stacks mapped to cfn template.
        :return: The list of cfn stacks.
        """
        new_list = []
        for val in dict_object.values():
            new_list = new_list + val
        return new_list

    def _get_cfn_template_file_name(self, cfn_template_path: str) -> str:
        """
        Returns tuple of cloud formation template file name and extension pair.
        :param cfn_template_path The cloud formation template path
        :return The cloud formation file name with no extension.
        """
        base_name = os.path.basename(cfn_template_path)
        (file_name, ext) = os.path.splitext(base_name)
        return file_name

    def get_s3_bucket_name(self, account_id: str, region_name: str) -> str:
        """
        Returns S3 bucket name based on given account id and region name.
        :param account_id: The AWS account id.
        :param region_name: The region name.
        :return: The S3 bucket name.
        """
        return s3_bucket_name_pattern.replace('<account_id>', account_id).replace('<region_name>', region_name)

    @staticmethod
    def _delete_resource(cfn_client, resource_to_delete: ResourceModel, all_resources: [], logger):
        """
         Deletes given resource and cfn stack mapped to this resource. It will wait till all
         dependent resources (if any) will be removed first before deleting given resource. In case if resource
         deletion is failed for any reason exception will be thrown and resource will be left to state 'DELETE_FAILED'.
        :param cfn_client: The cfn boto3 client.
        :param resource_to_delete: The resource to be deleted.
        :param all_resources: The list of all existing resources.
        :param logger: The logger.
        :return:
        """
        cfn_stack_name = resource_to_delete.cf_stack_name
        sleep_time_secs = 20
        try:

            ResourceModel.update_resource_status(resource_to_delete, ResourceModel.Status.DELETING)
            dependent_stack_name = ResourceTool._has_dependents(cfn_stack_name, all_resources, logger)
            while dependent_stack_name:
                logger.info(f'Waiting for stack [{dependent_stack_name}] to be deleted before '
                            f'deleting [{cfn_stack_name}], sleeping [{sleep_time_secs}] seconds.')
                time.sleep(sleep_time_secs)
                dependent_stack_name = ResourceTool._has_dependents(cfn_stack_name, ResourceModel.scan(), logger)
            # Delete stack.
            logger.info(f'Deleting [{cfn_stack_name}] stack.')
            ResourceTool._delete_stack(cfn_client, resource_to_delete)
            # Delete DDB resource record.
            resource_to_delete.delete()
        except Exception as e:
            logger.error(f'Failed to delete [{cfn_stack_name}] stack due to: {e}')
            ResourceModel.update_resource_status(resource_to_delete, ResourceModel.Status.DELETE_FAILED)

    @staticmethod
    def _has_dependents(cfn_stack_name: str, all_resources: [], logger) -> str:
        """
        Returns True if given cfn stack name has dependents, False otherwise.
        :param cfn_stack_name: The cfn stack name.
        :param all_resources: The list of all existing resources.
        :param logger: The logger.
        :return: True in dependent still exit, not deleted yet, False otherwise.
        """
        for resource in all_resources:
            if resource.cfn_dependency_stacks and cfn_stack_name in resource.cfn_dependency_stacks:
                if resource.status == ResourceModel.Status.DELETE_FAILED.name:
                    err_message = f'Stack [{cfn_stack_name}] deletion failed due to dependent ' \
                                  f'stack [{resource.cf_stack_name}] deletion failed.'
                    logger.error(err_message)
                    raise Exception(err_message)
                return resource.cf_stack_name
        return None

    @staticmethod
    def _delete_stack(cfn_client, resource: ResourceModel):
        """
        Deletes cfn stack for given resource.
        :param cfn_client: The cloud formation boto3 client.
        :param resource: The given resource.
        """
        try:
            stack_name = resource.cf_stack_name
            cfn_client.update_termination_protection(StackName=stack_name, EnableTerminationProtection=False)
            cfn_client.delete_stack(StackName=stack_name)
            waiter = cfn_client.get_waiter('stack_delete_complete')
            waiter.wait(StackName=stack_name)
        except ClientError as e:
            err_message = e.response['Error']['Message']
            if f'Stack [{stack_name}] does not exist' in err_message \
                    and e.response['Error']['Code'] == 'ValidationError':
                # Do nothing as stack for given name does not exist.
                pass
            else:
                logger.error(e)
                raise e

    def _delete_s3_files(self, bucket_name: str, stacks_to_delete: dict()):
        """
         Deletes file from S3 for given bucket name list of stacks mapped to cfn template name as key.
        :param bucket_name: The S3 bucket name.
        :param stacks_to_delete: The ist of stacks mapped to cfn template name as key.
        :return:
        """
        s3_keys_to_be_deleted = self._get_s3_keys_to_delete(stacks_to_delete)
        s3_objects_to_delete = []
        for f in s3_keys_to_be_deleted:
            s3_objects_to_delete.append({'Key': f})

        logger.info(f' Deleting [{len(s3_keys_to_be_deleted)}] cfn template(s) from s3 {s3_keys_to_be_deleted}')
        if len(s3_objects_to_delete) > 0:
            s3_bucket = self.s3_resource.Bucket(bucket_name)
            s3_bucket.delete_objects(Delete={'Objects': s3_objects_to_delete})

    def _get_s3_keys_to_delete(self, stacks_to_delete: dict()):
        """
        Returns list of S3 file keys to be deleted. In case if any stack for given S3 cfn template file
        exist this file will not be deleted with warning message.
        :param stacks_to_delete: The dict of stacks mapped to cfn template name as key.
        :return: The list of S3 files to be deleted from S3.
        """
        s3_keys_to_delete = []
        for key in stacks_to_delete:
            stack_exist = False
            for cfn_stack in stacks_to_delete[key]:
                if self._stack_exists(cfn_stack):
                    logger.warning(BgColors.WARNING + f" Stack [{cfn_stack}] still exists, cfn template file"
                                                      f" [{key}] will not be deleted from S3." + BgColors.ENDC)
                    stack_exist = True
            if not stack_exist:
                s3_keys_to_delete.append(key)
        return s3_keys_to_delete

    def _stack_exists(self, stack_name: str, required_status='DELETE_COMPLETE'):
        """
        Verifies if cfn stack for given name exist.
        :param stack_name: The cfn stack name to verify
        :param required_status: The required status in case if stack is till exist.
        :return: True  stack exists, False otherwise.
        """
        try:
            stacks_summary = self.cfn_client.describe_stacks(StackName=stack_name)
            stack_info = stacks_summary.get('Stacks')[0]
            return stack_name == stack_info.get('StackName') and stack_info.get('StackStatus') != required_status
        except ClientError as e:
            stack_not_found_error = f'Stack with id {stack_name} does not exist'
            error_received = e.response['Error']
            error_code_received = error_received.get('Code')
            error_message_received = error_received.get('Message')
            if error_code_received == 'ValidationError' and error_message_received == stack_not_found_error:
                return False
            logger.exception(f'Client error while describing stacks: {e}')
            raise
        except Exception:
            logger.exception('Error while checking stack')
            raise

    def _find_resource_dependents(self, resource_to_delete: ResourceModel, all_resources) -> []:
        """
        Returns dependents for resource which should be deleted. In case if resource which should be deleted
        has dependents than dependents should be deleted before this resources can be deleted.
        :param resource_to_delete: The resource to be deleted.
        :param all_resources: The list of all existing resources.
        :return: The dictionary of resources where key is template name, value is a list of cfn stacks created
        using this cfn template.
        """
        dependent_stacks = {}
        for dependent_resource in all_resources:
            cfn_template_name = self._get_cfn_template_file_name(dependent_resource.cf_template_name)
            if dependent_resource.cfn_dependency_stacks \
                    and resource_to_delete.cf_stack_name in dependent_resource.cfn_dependency_stacks:
                cfn_template_stacks = dependent_stacks.get(cfn_template_name)
                if not cfn_template_stacks:
                    cfn_template_stacks = []
                    dependent_stacks[cfn_template_name] = cfn_template_stacks
                cfn_template_stacks.append(dependent_resource.cf_stack_name)
        return dependent_stacks


def main(argv):
    cfn_template_names = None
    aws_profile_name = None
    command = None
    try:
        opts, args = getopt.getopt(argv, "ho:p:t:c:", ["help", "aws_profile=", "cfn_templates=", "command="])
    except getopt.GetoptError as err:
        logger.error(err)
        sys.exit(2)
    for o, a in opts:
        if o in ["-h", "--help"]:
            print(BgColors.HEADER + '------------------------------------------------------------------------\n'
                  'This tool is designed for manual integration test resource manipulation.\n'
                  '------------------------------------------------------------------------\n' + BgColors.ENDC)
            print('Example: '
                  'resource_manager/src/resource_tool.py -c <command> -t <cfn_template_name_1,cfn_template_name_2> -p '
                  '<aws_profile_name>\n'
                  '-c, --command (required): Command to perform against cloud formation resources for given template '
                  'names (DESTROY | DESTROY_ALL | LIST).\n'
                  '   - DESTROY - destroys resources for given template names (--cfn_templates)\n'
                  '   - DESTROY_ALL - destroys all resources, no need to provide template names\n'
                  '   - LIST - lists templates which are deployed with associated stacks\n'
                  '-t, --cfn_templates (required if --command DESTROY): Comma separated list of cloud formation '
                  'templates. Example: -t RdsCfnTemplate,S3Template (no file path/extension).\n'
                  '-p, --aws_profile (optional, if not given \'default\' is used): AWS profile name'
                  ' for boto3 session creation.')
            sys.exit(0)
        elif o in ["-p", "--aws_profile"]:
            aws_profile_name = a
        elif o in ["-t", "--cfn_template_names"]:
            cfn_template_names = a
        elif o in ["-c", "--command"]:
            command = Command.from_string(a)

    # Validate parameters
    if not command:
        logger.error(BgColors.FAIL + ' Required parameter [-c, --command] is not provided.' + BgColors.ENDC)
        sys.exit(2)
    elif not cfn_template_names and command == Command.DESTROY:
        logger.error(BgColors.FAIL + ' Required parameter [-t, --cfn_templates] is not provided.' + BgColors.ENDC)
        sys.exit(2)
    elif not aws_profile_name:
        logger.warning(BgColors.WARNING + ' AWS profile name is not provided '
                                          '[-p, --aws_profile] using [default].' + BgColors.ENDC)
        aws_profile_name = 'default'

    boto3_session = boto3.Session(profile_name=aws_profile_name)
    rt = ResourceTool(boto3_session)
    if command == Command.DESTROY:
        templates_to_process = cfn_template_names.split(',')
        logger.info(f' Executing command [{command.name}] for template names {templates_to_process}')
        rt.destroy_resources(templates_to_process)
    elif command == Command.DESTROY_ALL:
        logger.info(f' Executing command [{command.name}]')
        rt.destroy_resources()
    elif command == Command.LIST:
        logger.info(f' Executing command [{command.name}]')
        rt.list_resources()


if __name__ == "__main__":
    main(sys.argv[1:])
