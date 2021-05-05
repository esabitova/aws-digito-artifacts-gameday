import sys
import os
import boto3
import getopt
import logging
from enum import Enum
from resource_model import ResourceModel
from concurrent.futures import ThreadPoolExecutor
from constants import s3_bucket_name_pattern

logger = logging.getLogger('resource_tool.py')
logging.basicConfig(format='%(asctime)s %(name)s %(levelname)s:%(message)s', level=logging.INFO,
                    handlers=[logging.StreamHandler(sys.stdout)])


class BgColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Command(Enum):
    DESTROY = 0,
    LIST = 1

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
        caller_id = boto3_session.client('sts').get_caller_identity()
        self.account_id = caller_id.get('Account')
        self.region = boto3_session.region_name

    def list_existing_resources(self):
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

    def destroy_resources_by_template_names(self, cfn_template_names: []):
        """
        Destroys cloud formation stacks, deletes cfn template files from S3 and record from DDB based
        on list of given cfn template names.
        :param cfn_template_names: The list of cfn template names
        :return:
        """
        resources_to_delete = []
        stacks_to_delete = []
        s3_keys_to_delete = []
        existing_template_names = []
        for resource in ResourceModel.scan():
            cfn_file_name = self._get_cfn_template_file_name(resource.cf_template_name)
            existing_template_names.append(cfn_file_name)
            if cfn_file_name in cfn_template_names:
                resources_to_delete.append(resource)
                stacks_to_delete.append(resource.cf_stack_name)
                s3_keys_to_delete.append(resource.cf_template_name)

        # Dedup list of files
        s3_keys_to_delete = list(dict.fromkeys(s3_keys_to_delete))

        resource_count = len(resources_to_delete)
        if resource_count > 0:
            logger.info(f" Destroying [{resource_count}] cloud formation stacks {stacks_to_delete}")
            with ThreadPoolExecutor(max_workers=10) as t_executor:
                for index in range(resource_count):
                    resource = resources_to_delete[index]
                    t_executor.submit(ResourceTool._delete_cfn_stack, self.cfn_client, resource.cf_stack_name)

            bucket_name = s3_bucket_name_pattern.\
                replace('<account_id>', self.account_id).replace('<region_name>', self.region)
            logger.info(f' Deleting [{len(s3_keys_to_delete)}] cfn template(s) from s3 {s3_keys_to_delete}')
            self._delete_s3_files(bucket_name, s3_keys_to_delete)

            logger.info(f' Deleting [{resource_count}] resource(s) from data base.')
            for r in resources_to_delete:
                r.delete()
        else:
            logging.warning(BgColors.WARNING + f" Nothing to destroy due to NO resources for template names "
                                               f"{cfn_template_names} found." + BgColors.ENDC)

    def _get_cfn_template_file_name(self, cfn_template_path: str):
        """
        Returns tuple of cloud formation template file name and extension pair.
        :param cfn_template_path The cloud formation template path
        :return The cloud formation file name with no extension.
        """
        base_name = os.path.basename(cfn_template_path)
        (file_name, ext) = os.path.splitext(base_name)
        return file_name

    @staticmethod
    def _delete_cfn_stack(cfn_client, stack_name):
        """
        Deletes cloud formation stack which is associated with
        this class instance, waits till completion.
        :param stack_name The stack name to delete.
        """
        cfn_client.update_termination_protection(StackName=stack_name,
                                                 EnableTerminationProtection=False)
        cfn_client.delete_stack(StackName=stack_name)
        waiter = cfn_client.get_waiter('stack_delete_complete')
        waiter.wait(StackName=stack_name)

    def _delete_s3_files(self, bucket_name, files_to_delete: []):
        """
         Deletes file from S3 for given bucket name and list of files.
        :param bucket_name: The S3 bucket name.
        :param files_to_delete: The list of file to be deleted.
        :return:
        """
        objects = []
        for f in files_to_delete:
            objects.append({'Key': f})
        s3_bucket = self.s3_resource.Bucket(bucket_name)
        s3_bucket.delete_objects(Delete={'Objects': objects})


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
            print('Example: resource_tool.py -c <command> -t <cfn_template_name_1,cfn_template_name_2> -p '
                  '<aws_profile_name>\n'
                  '-c, --command (required): Command to perform against cloud formation resources for given template '
                  'names (DESTROY | LIST).\n'
                  '-t, --cfn_templates (required if --command=DESTROY): Comma separated list of cloud formation '
                  'templates. Example: -t RdsCfnTemplate,S3Template (no file path/extension).\n'
                  '-p, --aws_profile (optional): AWS profile name for boto3 session creation.')
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
        rt.destroy_resources_by_template_names(templates_to_process)
    elif command == Command.LIST:
        logger.info(f' Executing command [{command}]')
        rt.list_existing_resources()


if __name__ == "__main__":
    main(sys.argv[1:])
