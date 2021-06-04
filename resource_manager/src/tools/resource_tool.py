import boto3
import getopt
import logging
import sys
import os
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
            existing_template_names.get(cfn_file_name).append(resource.cf_stack_name)
        for key in existing_template_names:
            print(BgColors.OKBLUE + f'* {key} -> {existing_template_names[key]}' + BgColors.ENDC)

    def destroy_resources(self, cfn_template_names: [] = None):
        """
        Destroys cloud formation stacks, deletes cfn template files from S3 and record from DDB based
        on list of given cfn template names.
        :param cfn_template_names: The list of cfn template names
        :return:
        """
        resources_to_delete = []
        stacks_to_delete = {}
        for resource in ResourceModel.scan():
            cfn_file_name = self._get_cfn_template_file_name(resource.cf_template_name)
            # In case if cfn template list is given collect only template name related resources
            if cfn_template_names:
                if cfn_file_name in cfn_template_names:
                    resources_to_delete.append(resource)
                    if not stacks_to_delete.get(resource.cf_template_name):
                        stacks_to_delete[resource.cf_template_name] = []
                    stacks_to_delete.get(resource.cf_template_name).append(resource.cf_stack_name)
            # In case if cfn template list is  NOT given collect all resources
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
                    t_executor.submit(ResourceTool._delete_resource, self.cfn_client, resource)

            s3_bucket_name = self.get_s3_bucket_name(self.account_id, self.region)
            self._delete_s3_files(s3_bucket_name, stacks_to_delete)
        else:
            logger.warning(BgColors.WARNING + f" Nothing to destroy due to NO resources for template names "
                                              f"{cfn_template_names} found." + BgColors.ENDC)

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
        Create and return
        :param account_id:
        :param region_name:
        :return:
        """
        return s3_bucket_name_pattern.replace('<account_id>', account_id).replace('<region_name>', region_name)

    @staticmethod
    def _delete_resource(cfn_client, resource: ResourceModel):
        """
        Deletes cloud formation stack which is associated with
        this class instance, waits till completion.
        :param stack_name The stack name to delete.
        """
        # Delete stack.
        cfn_client.update_termination_protection(StackName=resource.cf_stack_name,
                                                 EnableTerminationProtection=False)
        cfn_client.delete_stack(StackName=resource.cf_stack_name)
        waiter = cfn_client.get_waiter('stack_delete_complete')
        waiter.wait(StackName=resource.cf_stack_name)
        # Delete DDB resource record.
        resource.delete()

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
        logger.info(f' Executing command [{command}] for template names {templates_to_process}')
        rt.destroy_resources(templates_to_process)
    elif command == Command.DESTROY_ALL:
        logger.info(f' Executing command [{command}]')
        rt.destroy_resources()
    elif command == Command.LIST:
        logger.info(f' Executing command [{command}]')
        rt.list_resources()


if __name__ == "__main__":
    main(sys.argv[1:])
