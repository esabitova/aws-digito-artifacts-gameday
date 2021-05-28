import unittest
import pytest
import resource_manager.src.config as config
import resource_manager.src.util.yaml_util as yaml_util
import resource_manager.src.constants as constants
from unittest.mock import patch, MagicMock, call, mock_open
from resource_manager.src.resource_pool import ResourcePool
from resource_manager.src.resource_model import ResourceModel


@pytest.mark.unit_test
class TestResourcePool(unittest.TestCase):

    def setUp(self):
        self.os_path_patcher = patch('os.path')
        self.os_path_mock = self.os_path_patcher.start()
        self.test_template_name = 'TestCfnTempName'
        self.test_bucket_name = 'test_bucket_name'
        self.dummy_test_session_id = 'dummy_test_session_id'
        self.os_path_mock.isfile.return_value = True
        self.s3_helper_mock = MagicMock()
        self.s3_helper_mock.get_bucket_name.return_value = self.test_bucket_name
        self.s3_helper_mock.get_file_content.return_value = None
        self.cfn_helper_mock = MagicMock()

        self.rm = ResourcePool(self.cfn_helper_mock, self.s3_helper_mock, dict(), self.dummy_test_session_id, {})

        self.file_data_dummy = '{"AWSTemplateFormatVersion": "2010-09-09",' \
                               '"Description": "Assume Roles for SSM automation execution.",' \
                               '"Outputs": {},' \
                               '"Resources": {}}'
        self.cfn_content_sha1 = yaml_util.get_yaml_content_sha1_hash(yaml_util.loads_yaml(self.file_data_dummy))
        self.cfn_input_param_sha1 = yaml_util.get_yaml_content_sha1_hash({'TestParamA': 'test_value'})
        self.mock_file_patcher = patch('builtins.open', mock_open(read_data=self.file_data_dummy))
        self.mock_file = self.mock_file_patcher.start()

    def tearDown(self):
        self.os_path_patcher.stop()
        self.mock_file_patcher.stop()
        config.pool_size = dict(default=1)

    def test_add_cfn_templates_success(self):
        self.os_path_mock.splitext.side_effect = [('TestTemplateA', 'yml'),
                                                  ('TestTemplateB', 'yml')]

        cfn_templates = "|CfnTemplatePath   |ResourceType|TestParamA|\n"\
                        "|TestTemplateA.yml |  ON_DEMAND |test_value|\n"\
                        "|TestTemplateB.yml |ASSUME_ROLE |          |"
        self.rm.add_cfn_templates(cfn_templates)
        self.assertEqual(len(self.rm.cfn_templates), 2)

    def test_add_cfn_templates_duplicate_name_fail(self):
        self.os_path_mock.splitext.return_value = ('TestTemplateA', 'yml')

        cfn_templates = "|CfnTemplatePath   |ResourceType|TestParamA|\n" \
                        "|TestTemplateA.yml |  ON_DEMAND |test_value|\n" \
                        "|TestTemplateA.yml |ASSUME_ROLE |          |"
        self.assertRaises(Exception, self.rm.add_cfn_templates, cfn_templates)

    def test_add_cfn_templates_missing_param_fail_1(self):
        self.os_path_mock.splitext.return_value = ('TestTemplateA', 'yml')

        cfn_templates = "|MyTestParam       |ResourceType|TestParamA|\n" \
                        "|TestTemplateA.yml |  ON_DEMAND |test_value|\n" \
                        "|TestTemplateB.yml |ASSUME_ROLE |          |"
        self.assertRaises(Exception, self.rm.add_cfn_templates, cfn_templates)

    def test_add_cfn_templates_missing_param_fail_2(self):
        self.os_path_mock.splitext.return_value = ('TestTemplateA', 'yml')

        cfn_templates = "|CfnTemplatePath   |MyTestParam |TestParamA|\n" \
                        "|TestTemplateA.yml |  ON_DEMAND |test_value|\n" \
                        "|TestTemplateB.yml |ASSUME_ROLE |          |"
        self.assertRaises(Exception, self.rm.add_cfn_templates, cfn_templates)

    @patch('resource_manager.src.resource_model.ResourceModel.query')
    @patch('resource_manager.src.resource_model.ResourceModel.create')
    def test_pull_resources_on_demand_by_template_name_missing_template_index_success(self, create_mock, query_mock):
        self.os_path_mock.splitext.return_value = (self.test_template_name, 'yml')
        r1 = MagicMock()
        r1.configure_mock(cf_stack_index=1,
                          type=ResourceModel.ResourceType.ON_DEMAND.name,
                          status=ResourceModel.Status.AVAILABLE.name,
                          cf_template_sha1=self.cfn_content_sha1,
                          cf_input_parameters_sha1=self.cfn_input_param_sha1)
        query_mock.return_value = [r1]

        r2 = MagicMock()
        r2.configure_mock(cf_stack_index=0,
                          type=ResourceModel.ResourceType.ON_DEMAND.name,
                          cf_template_sha1=self.cfn_content_sha1,
                          cf_input_parameters_sha1=self.cfn_input_param_sha1)
        create_mock.return_value = r2

        cfn_templates = '|CfnTemplatePath|ResourceType|TestParamA|\n' \
                        '|{}.yml         |   ON_DEMAND|test_value|'.format(self.test_template_name)
        self.rm.add_cfn_templates(cfn_templates)
        cfn_template = (self.test_template_name, self.rm.cfn_templates[self.test_template_name])
        resource = self.rm.pull_resource_by_template(cfn_template)

        self.assertEqual(resource.cf_stack_index, 0)
        self.assertEqual(resource.status, ResourceModel.Status.LEASED.name)
        r2.save.assert_called_once()

        self.s3_helper_mock.upload_file.assert_called_once()
        self.cfn_helper_mock.deploy_cf_stack.assert_called_once()

    @patch('resource_manager.src.resource_model.ResourceModel.query')
    def test_pull_resources_on_demand_by_template_name_success(self, query_mock):
        self.os_path_mock.splitext.return_value = (self.test_template_name, 'yml')
        config.pool_size[self.test_template_name] = 2
        r1 = MagicMock()
        r1.configure_mock(cf_stack_index=0,
                          type=ResourceModel.ResourceType.ON_DEMAND.name,
                          status=ResourceModel.Status.LEASED.name,
                          cf_template_sha1=self.cfn_content_sha1,
                          cf_input_parameters_sha1=self.cfn_input_param_sha1)

        r2 = MagicMock()
        r2.configure_mock(cf_stack_index=1,
                          type=ResourceModel.ResourceType.ON_DEMAND.name,
                          status=ResourceModel.Status.AVAILABLE.name,
                          cf_template_sha1=self.cfn_content_sha1,
                          cf_input_parameters_sha1=self.cfn_input_param_sha1)
        query_mock.return_value = [r1, r2]

        cfn_templates = '|CfnTemplatePath|ResourceType|TestParamA|\n' \
                        '|{}.yml         |   ON_DEMAND|test_value|'.format(self.test_template_name)
        self.rm.add_cfn_templates(cfn_templates)
        cfn_template = (self.test_template_name, self.rm.cfn_templates[self.test_template_name])
        resource = self.rm.pull_resource_by_template(cfn_template)

        self.assertEqual(resource.cf_stack_index, 1)
        self.assertEqual(resource.status, ResourceModel.Status.LEASED.name)
        r2.save.assert_called_once()
        r1.save.assert_not_called()

    @patch('resource_manager.src.resource_model.ResourceModel.query')
    def test_pull_resources_dedicated_by_template_name_success(self, query_mock):
        self.os_path_mock.splitext.return_value = (self.test_template_name, 'yml')
        config.pool_size[self.test_template_name] = 2
        r1 = MagicMock()
        r1.configure_mock(cf_stack_index=0,
                          type=ResourceModel.ResourceType.DEDICATED.name,
                          status=ResourceModel.Status.LEASED.name,
                          cf_template_sha1=self.cfn_content_sha1,
                          cf_input_parameters_sha1=self.cfn_input_param_sha1)

        r2 = MagicMock()
        r2.configure_mock(cf_stack_index=1,
                          type=ResourceModel.ResourceType.DEDICATED.name,
                          status=ResourceModel.Status.DELETED.name,
                          cf_template_sha1=self.cfn_content_sha1,
                          cf_input_parameters_sha1=self.cfn_input_param_sha1)
        query_mock.return_value = [r1, r2]

        cfn_templates = '|CfnTemplatePath|ResourceType|TestParamA|\n' \
                        '|{}.yml         |   DEDICATED|test_value|'.format(self.test_template_name)
        self.rm.add_cfn_templates(cfn_templates)
        cfn_template = (self.test_template_name, self.rm.cfn_templates[self.test_template_name])
        resource = self.rm.pull_resource_by_template(cfn_template)

        self.assertEqual(resource.cf_stack_index, 1)
        self.assertEqual(resource.status, ResourceModel.Status.LEASED.name)
        r1.save.assert_not_called()
        self.assertEqual(r2.save.call_count, 2)

    @patch('resource_manager.src.resource_model.ResourceModel.query')
    def test_pull_resources_mixed_types_by_template_name_success(self, query_mock):
        self.os_path_mock.splitext.return_value = (self.test_template_name, 'yml')
        r1 = MagicMock()
        r1.configure_mock(cf_stack_index=0,
                          type=ResourceModel.ResourceType.ON_DEMAND.name,
                          status=ResourceModel.Status.AVAILABLE.name,
                          cf_template_sha1=self.cfn_content_sha1,
                          cf_input_parameters_sha1=self.cfn_input_param_sha1)

        r2 = MagicMock()
        r2.configure_mock(cf_stack_index=0,
                          type=ResourceModel.ResourceType.SHARED.name,
                          status=ResourceModel.Status.AVAILABLE.name,
                          cf_template_sha1=self.cfn_content_sha1,
                          cf_input_parameters_sha1=self.cfn_input_param_sha1)
        query_mock.return_value = [r1, r2]

        cfn_templates = '|CfnTemplatePath|ResourceType|TestParamA|\n' \
                        '|{}.yml         |      SHARED|test_value|'.format(self.test_template_name)
        self.rm.add_cfn_templates(cfn_templates)
        cfn_template = (self.test_template_name, self.rm.cfn_templates[self.test_template_name])
        resource = self.rm.pull_resource_by_template(cfn_template)

        self.assertEqual(resource.cf_stack_index, 0)
        self.assertEqual(resource.status, ResourceModel.Status.AVAILABLE.name)
        self.assertEqual(resource.type, ResourceModel.ResourceType.SHARED.name)
        r2.save.assert_not_called()
        r1.save.assert_not_called()

    @patch('resource_manager.src.resource_model.ResourceModel.query')
    def test_pull_resources_on_demand_by_template_name_cfn_param_sha1_not_equal_success(self, query_mock):
        self.os_path_mock.splitext.return_value = (self.test_template_name, 'yml')
        config.pool_size[self.test_template_name] = 2

        r1 = MagicMock()
        r1.configure_mock(cf_stack_index=0,
                          type=ResourceModel.ResourceType.ON_DEMAND.name,
                          status=ResourceModel.Status.LEASED.name,
                          cf_template_sha1=self.cfn_content_sha1,
                          cf_input_parameters_sha1=self.cfn_input_param_sha1)

        r2 = MagicMock()
        r2.configure_mock(cf_stack_index=1,
                          type=ResourceModel.ResourceType.ON_DEMAND.name,
                          status=ResourceModel.Status.AVAILABLE.name,
                          cf_template_sha1=self.cfn_content_sha1,
                          cf_input_parameters_sha1="not_equal_param_sha1")
        query_mock.return_value = [r1, r2]

        cfn_templates = '|CfnTemplatePath|ResourceType|TestParamA|\n' \
                        '|{}.yml         |   ON_DEMAND|test_value|'.format(self.test_template_name)
        self.rm.add_cfn_templates(cfn_templates)
        cfn_template = (self.test_template_name, self.rm.cfn_templates[self.test_template_name])
        resource = self.rm.pull_resource_by_template(cfn_template)

        self.assertEqual(resource.cf_stack_index, 1)
        self.assertEqual(resource.status, ResourceModel.Status.LEASED.name)
        self.assertEqual(r2.save.call_count, 2)
        r1.save.assert_not_called()

    @patch('resource_manager.src.resource_model.ResourceModel.query')
    def test_pull_resources_on_demand_by_template_name_cfn_template_sha1_not_equal_success(self, query_mock):
        self.os_path_mock.splitext.return_value = (self.test_template_name, 'yml')
        config.pool_size[self.test_template_name] = 2

        r1 = MagicMock()
        r1.configure_mock(cf_stack_index=0,
                          type=ResourceModel.ResourceType.ON_DEMAND.name,
                          status=ResourceModel.Status.LEASED.name,
                          cf_template_sha1=self.cfn_content_sha1,
                          cf_input_parameters_sha1=self.cfn_input_param_sha1)

        r2 = MagicMock()
        r2.configure_mock(cf_stack_index=1,
                          type=ResourceModel.ResourceType.ON_DEMAND.name,
                          status=ResourceModel.Status.AVAILABLE.name,
                          cf_template_sha1="not_equal_cfn_template_sha1",
                          cf_input_parameters_sha1=self.cfn_input_param_sha1)
        query_mock.return_value = [r1, r2]

        cfn_templates = '|CfnTemplatePath|ResourceType|TestParamA|\n' \
                        '|{}.yml         |   ON_DEMAND|test_value|'.format(self.test_template_name)
        self.rm.add_cfn_templates(cfn_templates)
        cfn_template = (self.test_template_name, self.rm.cfn_templates[self.test_template_name])
        resource = self.rm.pull_resource_by_template(cfn_template)

        self.assertEqual(resource.cf_stack_index, 1)
        self.assertEqual(resource.status, ResourceModel.Status.LEASED.name)
        self.assertEqual(r2.save.call_count, 2)
        r1.save.assert_not_called()

    @patch('resource_manager.src.resource_model.ResourceModel.query')
    @patch('resource_manager.src.resource_model.ResourceModel.create')
    def test_pull_resources_on_demand_by_template_name_create_success(self, create_mock, query_mock):
        self.os_path_mock.splitext.return_value = (self.test_template_name, 'yml')
        config.pool_size[self.test_template_name] = 2

        r1 = MagicMock()
        r1.configure_mock(cf_stack_index=0,
                          type=ResourceModel.ResourceType.ON_DEMAND.name,
                          status=ResourceModel.Status.LEASED.name)
        query_mock.return_value = [r1]

        r2 = MagicMock()
        r2.configure_mock(cf_stack_index=1,
                          type=ResourceModel.ResourceType.ON_DEMAND.name,
                          status=ResourceModel.Status.AVAILABLE.name)
        create_mock.return_value = r2

        cfn_templates = '|CfnTemplatePath|ResourceType|TestParamA|\n' \
                        '|{}.yml         |   ON_DEMAND|test_value|'.format(self.test_template_name)
        self.rm.add_cfn_templates(cfn_templates)
        cfn_template = (self.test_template_name, self.rm.cfn_templates[self.test_template_name])
        resource = self.rm.pull_resource_by_template(cfn_template)

        self.assertEqual(resource.cf_stack_index, 1)
        self.assertEqual(resource.status, ResourceModel.Status.LEASED.name)
        r2.save.assert_called_once()

        self.s3_helper_mock.upload_file.assert_called_once()
        self.cfn_helper_mock.deploy_cf_stack.assert_called_once()

    @patch('resource_manager.src.resource_model.ResourceModel.query')
    def test_pull_resources_on_demand_by_template_name_timeout_fail(self, query_mock):
        self.os_path_mock.splitext.return_value = (self.test_template_name, 'yml')
        constants.wait_time_out_secs = 2
        constants.sleep_time_secs = 1
        config.pool_size[self.test_template_name] = 2

        r1 = MagicMock()
        r1.configure_mock(cf_stack_index=0,
                          type=ResourceModel.ResourceType.ON_DEMAND.name,
                          status=ResourceModel.Status.LEASED.name)

        r2 = MagicMock()
        r2.configure_mock(cf_stack_index=1,
                          type=ResourceModel.ResourceType.ON_DEMAND.name,
                          status=ResourceModel.Status.LEASED.name)
        query_mock.return_value = [r1, r2]

        cfn_templates = '|CfnTemplatePath|ResourceType|TestParamA|\n' \
                        '|{}.yml         |   ON_DEMAND|test_value|'.format(self.test_template_name)
        self.rm.add_cfn_templates(cfn_templates)
        cfn_template = (self.test_template_name, self.rm.cfn_templates[self.test_template_name])

        self.assertRaises(Exception, self.rm.pull_resource_by_template, cfn_template)

    @patch('resource_manager.src.resource_model.ResourceModel.query')
    def test_pull_resources_on_demand_success(self, query_mock):
        config.pool_size[self.test_template_name] = 2
        config.pool_size[self.test_template_name + '_1'] = 1

        base_names = {
            self.test_template_name + '.yml': self.test_template_name + '.yml',
            self.test_template_name + '_1.yml': self.test_template_name + '_1.yml'
        }
        self.os_path_mock.basename.side_effect = lambda template_name: base_names.get(template_name)

        file_names = {
            self.test_template_name + '.yml': (self.test_template_name, 'yml'),
            self.test_template_name + '_1.yml': (self.test_template_name + '_1', 'yml')
        }
        self.os_path_mock.splitext.side_effect = lambda template_name: file_names.get(template_name)

        r1 = MagicMock()
        r1.configure_mock(cf_stack_index=0,
                          type=ResourceModel.ResourceType.ON_DEMAND.name,
                          status=ResourceModel.Status.AVAILABLE.name,
                          cf_template_sha1=self.cfn_content_sha1,
                          cf_input_parameters_sha1=self.cfn_input_param_sha1)

        r2 = MagicMock()
        r2.configure_mock(cf_stack_index=1,
                          type=ResourceModel.ResourceType.ON_DEMAND.name,
                          status=ResourceModel.Status.LEASED.name,
                          cf_template_sha1=self.cfn_content_sha1,
                          cf_input_parameters_sha1=self.cfn_input_param_sha1)

        r3 = MagicMock()
        r3.configure_mock(cf_stack_index=0,
                          type=ResourceModel.ResourceType.ON_DEMAND.name,
                          status=ResourceModel.Status.AVAILABLE.name,
                          cf_template_sha1=self.cfn_content_sha1,
                          cf_input_parameters_sha1=self.cfn_input_param_sha1)

        records_side_effect_map = {
            self.test_template_name + '.yml': [r1, r2],
            self.test_template_name + '_1.yml': [r3]
        }
        query_mock.side_effect = lambda cf_template_name: records_side_effect_map.get(cf_template_name)

        cfn_templates = '|CfnTemplatePath|ResourceType|TestParamA|\n' \
                        '|{}.yml         |   ON_DEMAND|test_value|\n'\
                        '|{}_1.yml       |   ON_DEMAND|test_value|'.format(self.test_template_name,
                                                                           self.test_template_name)
        self.rm.add_cfn_templates(cfn_templates)
        resources = self.rm.pull_resources()
        self.assertEqual(len(resources), 2)
        for cfn_name in resources.keys():
            self.assertEqual(resources[cfn_name][ResourcePool.CFN_RESOURCE_PARAM].status,
                             ResourceModel.Status.LEASED.name)
        r3.save.assert_called_once()
        r1.save.assert_called_once()

    @patch('resource_manager.src.resource_model.ResourceModel.query')
    @patch('resource_manager.src.resource_model.ResourceModel.create')
    def test_pull_resources_on_demand_create_success(self, create_mock, query_mock):

        config.pool_size[self.test_template_name] = 2
        config.pool_size[self.test_template_name + '_1'] = 1

        base_names = {
            self.test_template_name + '.yml': self.test_template_name + '.yml',
            self.test_template_name + '_1.yml': self.test_template_name + '_1.yml'
        }
        self.os_path_mock.basename.side_effect = lambda template_name: base_names.get(template_name)

        file_names = {
            self.test_template_name + '.yml': (self.test_template_name, 'yml'),
            self.test_template_name + '_1.yml': (self.test_template_name + '_1', 'yml')
        }
        self.os_path_mock.splitext.side_effect = lambda template_name: file_names.get(template_name)

        r1 = MagicMock()
        r1.configure_mock(cf_stack_index=0,
                          status=ResourceModel.Status.AVAILABLE.name,
                          type=ResourceModel.ResourceType.ON_DEMAND.name,
                          cf_template_sha1=self.cfn_content_sha1,
                          cf_input_parameters_sha1=self.cfn_input_param_sha1)

        r2 = MagicMock()
        r2.configure_mock(cf_stack_index=1,
                          status=ResourceModel.Status.LEASED.name,
                          type=ResourceModel.ResourceType.ON_DEMAND.name,
                          cf_template_sha1=self.cfn_content_sha1,
                          cf_input_parameters_sha1=self.cfn_input_param_sha1)

        records_side_effect_map = {
            self.test_template_name + '.yml': [r1, r2],
            self.test_template_name + '_1.yml': []
        }
        query_mock.side_effect = lambda cf_template_name: records_side_effect_map.get(cf_template_name)

        mock = MagicMock()
        mock.configure_mock(cf_stack_index=0, status=ResourceModel.Status.AVAILABLE.name)
        create_mock.return_value = mock

        cfn_templates = '|CfnTemplatePath|ResourceType|TestParamA|\n' \
                        '|{}.yml         |   ON_DEMAND|test_value|\n' \
                        '|{}_1.yml       |   ON_DEMAND|test_value|'.format(self.test_template_name,
                                                                           self.test_template_name)
        self.rm.add_cfn_templates(cfn_templates)
        resources = self.rm.pull_resources()
        self.assertEqual(len(resources), 2)
        for cfn_name in resources.keys():
            self.assertEqual(resources[cfn_name][ResourcePool.CFN_RESOURCE_PARAM].status,
                             ResourceModel.Status.LEASED.name)
        self.s3_helper_mock.upload_file.assert_called_once()
        self.cfn_helper_mock.deploy_cf_stack.assert_called_once()

    @patch('resource_manager.src.resource_model.ResourceModel.query')
    @patch('resource_manager.src.resource_model.ResourceModel.create')
    def test_pull_resources_dedicated_create_success(self, create_mock, query_mock):
        self.os_path_mock.splitext.return_value = (self.test_template_name, 'yml')
        config.pool_size[self.test_template_name] = 2
        r1 = MagicMock()
        r1.configure_mock(cf_stack_index=0,
                          status=ResourceModel.Status.LEASED.name,
                          type=ResourceModel.ResourceType.DEDICATED.name,
                          cf_template_sha1=self.cfn_content_sha1,
                          cf_input_parameters_sha1=self.cfn_input_param_sha1)

        client_side_effect_map = {
            self.test_template_name: [r1],
        }
        query_mock.side_effect = lambda cf_template_name: client_side_effect_map.get(cf_template_name)

        mock = MagicMock()
        mock.configure_mock(cf_stack_index=1,
                            status=ResourceModel.Status.CREATING.name,
                            type=ResourceModel.ResourceType.DEDICATED.name,
                            cf_template_sha1=self.cfn_content_sha1,
                            cf_input_parameters_sha1=self.cfn_input_param_sha1)
        create_mock.return_value = mock

        cfn_templates = '|CfnTemplatePath|ResourceType|TestParamA|\n' \
                        '|{}.yml         |   DEDICATED|test_value|\n'.format(self.test_template_name)
        self.rm.add_cfn_templates(cfn_templates)

        resources = self.rm.pull_resources()
        self.assertEqual(len(resources), 1)
        for cfn_name in resources.keys():
            self.assertEqual(resources[cfn_name][ResourcePool.CFN_RESOURCE_PARAM].status,
                             ResourceModel.Status.LEASED.name)

        self.s3_helper_mock.upload_file.assert_called_once()
        self.cfn_helper_mock.deploy_cf_stack.assert_called_once()

    @patch('resource_manager.src.resource_model.ResourceModel.query')
    @patch('resource_manager.src.resource_model.ResourceModel.create')
    def test_pull_resources_shared_create_success(self, create_mock, query_mock):
        config.pool_size[self.test_template_name] = 2
        config.pool_size[self.test_template_name + '_1'] = 1

        base_names = {
            self.test_template_name + '.yml': self.test_template_name + '.yml',
            self.test_template_name + '_1.yml': self.test_template_name + '_1.yml'
        }
        self.os_path_mock.basename.side_effect = lambda template_name: base_names.get(template_name)

        file_names = {
            self.test_template_name + '.yml': (self.test_template_name, 'yml'),
            self.test_template_name + '_1.yml': (self.test_template_name + '_1', 'yml')
        }
        self.os_path_mock.splitext.side_effect = lambda template_name: file_names.get(template_name)

        r1 = MagicMock()
        r1.configure_mock(cf_stack_index=0,
                          status=ResourceModel.Status.AVAILABLE.name,
                          type=ResourceModel.ResourceType.SHARED.name,
                          cf_template_sha1=self.cfn_content_sha1,
                          cf_input_parameters_sha1=self.cfn_input_param_sha1)

        records_side_effect_map = {
            self.test_template_name + '.yml': [r1],
            self.test_template_name + '_1.yml': []
        }
        query_mock.side_effect = lambda cf_template_name: records_side_effect_map.get(cf_template_name)

        mock = MagicMock()
        mock.configure_mock(cf_stack_index=0, status=ResourceModel.Status.AVAILABLE.name)
        create_mock.return_value = mock

        cfn_templates = '|CfnTemplatePath|ResourceType|TestParamA|\n' \
                        '|{}.yml         |      SHARED|test_value|\n' \
                        '|{}_1.yml       |      SHARED|test_value|'.format(self.test_template_name,
                                                                           self.test_template_name)
        self.rm.add_cfn_templates(cfn_templates)
        resources = self.rm.pull_resources()
        self.assertEqual(len(resources), 2)
        for cfn_name in resources.keys():
            self.assertEqual(resources[cfn_name][ResourcePool.CFN_RESOURCE_PARAM].status,
                             ResourceModel.Status.AVAILABLE.name)

        self.s3_helper_mock.upload_file.assert_called_once()
        self.cfn_helper_mock.deploy_cf_stack.assert_called_once()

    @patch('resource_manager.src.resource_model.ResourceModel.query')
    def test_get_cf_output_params_success(self, query_mock):

        config.pool_size[self.test_template_name] = 2
        config.pool_size[self.test_template_name + '_1'] = 1

        base_names = {
            self.test_template_name + '.yml': self.test_template_name + '.yml',
            self.test_template_name + '_1.yml': self.test_template_name + '_1.yml'
        }
        self.os_path_mock.basename.side_effect = lambda template_name: base_names.get(template_name)

        file_names = {
            self.test_template_name + '.yml': (self.test_template_name, 'yml'),
            self.test_template_name + '_1.yml': (self.test_template_name + '_1', 'yml')
        }
        self.os_path_mock.splitext.side_effect = lambda template_name: file_names.get(template_name)

        r1 = MagicMock()
        r1.configure_mock(cf_stack_index=0, status=ResourceModel.Status.AVAILABLE.name,
                          cf_template_name=self.test_template_name,
                          type=ResourceModel.ResourceType.ON_DEMAND.name,
                          cf_template_sha1=self.cfn_content_sha1,
                          cf_input_parameters_sha1=self.cfn_input_param_sha1,
                          attribute_values={'cf_output_parameters': [{'OutputKey': 'test_key_1',
                                                                      'OutputValue': 'test_value_1'}]})
        r2 = MagicMock()
        r2.configure_mock(cf_stack_index=1, status=ResourceModel.Status.LEASED.name,
                          cf_template_name=self.test_template_name,
                          type=ResourceModel.ResourceType.ON_DEMAND.name,
                          cf_template_sha1=self.cfn_content_sha1,
                          cf_input_parameters_sha1=self.cfn_input_param_sha1,
                          attribute_values={'cf_output_parameters': [{'OutputKey': 'test_key_2',
                                                                      'OutputValue': 'test_value_2'}]})
        r3 = MagicMock()
        r3.configure_mock(cf_stack_index=0, status=ResourceModel.Status.AVAILABLE.name,
                          cf_template_name=self.test_template_name + '_1',
                          type=ResourceModel.ResourceType.ON_DEMAND.name,
                          cf_template_sha1=self.cfn_content_sha1,
                          cf_input_parameters_sha1=self.cfn_input_param_sha1,
                          attribute_values={'cf_output_parameters': [{'OutputKey': 'test_key_3',
                                                                      'OutputValue': 'test_value_3'}]})
        records_side_effect_map = {
            self.test_template_name + '.yml': [r1, r2],
            self.test_template_name + '_1.yml': [r3]
        }
        query_mock.side_effect = lambda cf_template_name: records_side_effect_map.get(cf_template_name)

        cfn_templates = '|CfnTemplatePath|ResourceType|TestParamA|\n' \
                        '|{}.yml         |   ON_DEMAND|test_value|\n' \
                        '|{}_1.yml       |   ON_DEMAND|test_value|'.format(self.test_template_name,
                                                                           self.test_template_name)
        self.rm.add_cfn_templates(cfn_templates)

        resources_params = self.rm.get_cfn_output_params()
        self.assertEqual(len(resources_params), 2)
        self.assertIsNotNone(resources_params.get(self.test_template_name + '_1'))
        self.assertIsNotNone(resources_params.get(self.test_template_name))

        self.assertIsNotNone(resources_params.get(self.test_template_name).get('test_key_1'))
        self.assertIsNotNone(resources_params.get(self.test_template_name + '_1').get('test_key_3'))
        self.assertEqual(resources_params.get(self.test_template_name + '_1')['test_key_3'], 'test_value_3')
        self.assertEqual(resources_params.get(self.test_template_name)['test_key_1'], 'test_value_1')
        r3.save.assert_called_once()
        r1.save.assert_called_once()

    @patch('resource_manager.src.resource_model.ResourceModel.query')
    def test_pull_resources_with_cfn_referenced_params_success(self, query_mock):

        config.pool_size[self.test_template_name] = 2
        config.pool_size[self.test_template_name + '_1'] = 1

        base_names = {
            self.test_template_name + '.yml': self.test_template_name + '.yml',
            self.test_template_name + '_1.yml': self.test_template_name + '_1.yml'
        }
        self.os_path_mock.basename.side_effect = lambda template_name: base_names.get(template_name)

        file_names = {
            self.test_template_name + '.yml': (self.test_template_name, 'yml'),
            self.test_template_name + '_1.yml': (self.test_template_name + '_1', 'yml')
        }
        self.os_path_mock.splitext.side_effect = lambda template_name: file_names.get(template_name)

        r1 = MagicMock()
        r1.configure_mock(cf_stack_index=0, status=ResourceModel.Status.AVAILABLE.name,
                          cf_template_name=self.test_template_name,
                          type=ResourceModel.ResourceType.ON_DEMAND.name,
                          cf_template_sha1=self.cfn_content_sha1,
                          cf_input_parameters_sha1=self.cfn_input_param_sha1,
                          attribute_values={'cf_output_parameters': [{'OutputKey': 'test_key_1',
                                                                      'OutputValue': 'test_value'}]})
        r2 = MagicMock()
        r2.configure_mock(cf_stack_index=1, status=ResourceModel.Status.LEASED.name,
                          cf_template_name=self.test_template_name,
                          type=ResourceModel.ResourceType.ON_DEMAND.name,
                          cf_template_sha1=self.cfn_content_sha1,
                          cf_input_parameters_sha1=self.cfn_input_param_sha1,
                          attribute_values={'cf_output_parameters': [{'OutputKey': 'test_key_1',
                                                                      'OutputValue': 'test_value_2'}]})
        r3 = MagicMock()
        r3.configure_mock(cf_stack_index=0, status=ResourceModel.Status.AVAILABLE.name,
                          cf_template_name=self.test_template_name + '_1',
                          type=ResourceModel.ResourceType.ON_DEMAND.name,
                          cf_template_sha1=self.cfn_content_sha1,
                          cf_input_parameters_sha1=self.cfn_input_param_sha1,
                          attribute_values={'cf_output_parameters': [{'OutputKey': 'test_key_3',
                                                                      'OutputValue': 'test_value_3'}]})
        records_side_effect_map = {
            self.test_template_name + '.yml': [r1, r2],
            self.test_template_name + '_1.yml': [r3]
        }
        query_mock.side_effect = lambda cf_template_name: records_side_effect_map.get(cf_template_name)

        cfn_templates = '|CfnTemplatePath      |ResourceType|                               TestParamA|\n' \
                        '|TestCfnTempName.yml  |   ON_DEMAND|                               test_value|\n' \
                        '|TestCfnTempName_1.yml|   ON_DEMAND|{{cfn-output:TestCfnTempName>test_key_1}}|'
        self.rm.add_cfn_templates(cfn_templates)

        resources = self.rm.pull_resources()
        self.assertEqual(len(resources), 2)
        for cfn_name in resources.keys():
            self.assertEqual(resources[cfn_name][ResourcePool.CFN_RESOURCE_PARAM].status,
                             ResourceModel.Status.LEASED.name)

        r3.save.assert_called_once()
        r1.save.assert_called_once()

    @patch('resource_manager.src.resource_model.ResourceModel.scan')
    def test_fix_stalled_resources_success(self, scan_mock):
        r1 = MagicMock()
        r1.configure_mock(status=ResourceModel.Status.LEASED.name,
                          test_session_id=self.dummy_test_session_id)
        r2 = MagicMock()
        r2.configure_mock(status=ResourceModel.Status.CREATING.name,
                          test_session_id=self.dummy_test_session_id)
        scan_mock.return_value = [r1, r2]

        self.rm.fix_stalled_resources()

        self.assertEqual(r1.status, ResourceModel.Status.AVAILABLE.name)
        r2.delete.assert_called_once()

    @patch('resource_manager.src.resource_model.ResourceModel.scan')
    def test_fix_stalled_resources_no_session_success(self, scan_mock):
        r1 = MagicMock()
        r1.configure_mock(status=ResourceModel.Status.LEASED.name,
                          test_session_id='dummy_test_session_id_a')
        r2 = MagicMock()
        r2.configure_mock(status=ResourceModel.Status.CREATING.name,
                          test_session_id='dummy_test_session_id_b')
        scan_mock.return_value = [r1, r2]
        rm = ResourcePool(self.cfn_helper_mock, self.s3_helper_mock, dict(), None, None)
        rm.fix_stalled_resources()

        self.assertEqual(r1.status, ResourceModel.Status.AVAILABLE.name)
        r2.delete.assert_called_once()

    @patch('resource_manager.src.resource_model.ResourceModel.scan')
    def test_fix_stalled_resources_no_deletion_success(self, scan_mock):
        r1 = MagicMock()
        r1.configure_mock(status=ResourceModel.Status.LEASED.name,
                          test_session_id=self.dummy_test_session_id)
        r2 = MagicMock()
        r2.configure_mock(status=ResourceModel.Status.CREATING.name,
                          test_session_id='dummy_bad_test_session_id')
        scan_mock.return_value = [r1, r2]

        self.rm.fix_stalled_resources()

        self.assertEqual(r1.status, ResourceModel.Status.AVAILABLE.name)
        r2.delete.assert_not_called()

    @patch('resource_manager.src.resource_model.ResourceModel.scan')
    @patch('resource_manager.src.resource_model.ResourceModel.delete_table')
    def test_destroy_all_resources_success(self, delete_table_mock, scan_mock):
        r1 = MagicMock()
        r1.configure_mock(cf_stack_name='stack_name_1')

        r2 = MagicMock()
        r2.configure_mock(cf_stack_name='stack_name_2')
        scan_mock.return_value = [r1, r2]

        self.rm.destroy_all_resources()

        self.cfn_helper_mock.delete_cf_stack.assert_has_calls([call('stack_name_1'), call('stack_name_2')])
        self.s3_helper_mock.delete_bucket.assert_called_once()
        self.s3_helper_mock.get_bucket_name.assert_called_once()
        delete_table_mock.assert_called_once()

    def test_resource_type_from_string_success(self):
        actual_type = ResourceModel.ResourceType.from_string('ON_DEMAND')
        self.assertEqual(actual_type, ResourceModel.ResourceType.ON_DEMAND)

    def test_resource_type_from_string_fail(self):
        self.assertRaises(Exception, ResourceModel.ResourceType.from_string, 'NOT_SUPPORTED')

    def test_get_resource_pool_size_on_demand_custom_success(self):
        expected_pool_size = 10
        custom_pool_size = dict(TesTemplateA=expected_pool_size)
        rm = ResourcePool(self.cfn_helper_mock, self.s3_helper_mock, custom_pool_size, 'dummy_test_session_id', None)
        actual_pool_size = rm._get_resource_pool_size('TesTemplateA', ResourceModel.ResourceType.ON_DEMAND)
        self.assertEqual(actual_pool_size, expected_pool_size)

    def test_get_resource_pool_size_on_demand_custom_override_config_success(self):
        expected_pool_size = 10
        config.pool_size['TesTemplateA'] = 5
        custom_pool_size = dict(TesTemplateA=expected_pool_size)
        rm = ResourcePool(self.cfn_helper_mock, self.s3_helper_mock, custom_pool_size, 'dummy_test_session_id', None)
        actual_pool_size = rm._get_resource_pool_size('TesTemplateA', ResourceModel.ResourceType.ON_DEMAND)
        self.assertEqual(actual_pool_size, expected_pool_size)

    def test_get_resource_pool_size_dedicated_custom_override_config_success(self):
        expected_pool_size = 10
        config.pool_size['TesTemplateA'] = 5
        custom_pool_size = dict(TesTemplateA=expected_pool_size)
        rm = ResourcePool(self.cfn_helper_mock, self.s3_helper_mock, custom_pool_size, 'dummy_test_session_id', None)
        actual_pool_size = rm._get_resource_pool_size('TesTemplateA', ResourceModel.ResourceType.DEDICATED)
        self.assertEqual(actual_pool_size, expected_pool_size)

    def test_get_resource_pool_size_on_demand_config_success(self):
        expected_pool_size = 6
        custom_pool_size = dict()
        config.pool_size['TesTemplateA'] = expected_pool_size
        rm = ResourcePool(self.cfn_helper_mock, self.s3_helper_mock, custom_pool_size, 'dummy_test_session_id', None)
        actual_pool_size = rm._get_resource_pool_size('TesTemplateA', ResourceModel.ResourceType.ON_DEMAND)
        self.assertEqual(actual_pool_size, expected_pool_size)

    def test_get_resource_pool_size_shared_config_success(self):
        expected_pool_size = 1
        custom_pool_size = dict()
        config.pool_size['TesTemplateA'] = 6
        rm = ResourcePool(self.cfn_helper_mock, self.s3_helper_mock, custom_pool_size, 'dummy_test_session_id', None)
        actual_pool_size = rm._get_resource_pool_size('TesTemplateA', ResourceModel.ResourceType.SHARED)
        self.assertEqual(actual_pool_size, expected_pool_size)

    def test_get_resource_pool_size_dedicated_config_success(self):
        expected_pool_size = 6
        custom_pool_size = dict()
        config.pool_size['TesTemplateA'] = 6
        rm = ResourcePool(self.cfn_helper_mock, self.s3_helper_mock, custom_pool_size, 'dummy_test_session_id', None)
        actual_pool_size = rm._get_resource_pool_size('TesTemplateA', ResourceModel.ResourceType.DEDICATED)
        self.assertEqual(actual_pool_size, expected_pool_size)

    def test_get_resource_pool_size_assume_role_config_success(self):
        expected_pool_size = 1
        custom_pool_size = dict()
        config.pool_size['TesTemplateA'] = 6
        rm = ResourcePool(self.cfn_helper_mock, self.s3_helper_mock, custom_pool_size, 'dummy_test_session_id', None)
        actual_pool_size = rm._get_resource_pool_size('TesTemplateA', ResourceModel.ResourceType.ASSUME_ROLE)
        self.assertEqual(actual_pool_size, expected_pool_size)

    def test_release_resources_success(self):
        on_demand = MagicMock()
        on_demand.configure_mock(cf_stack_index=1,
                                 type=ResourceModel.ResourceType.ON_DEMAND.name,
                                 status=ResourceModel.Status.LEASED.name,
                                 cf_template_sha1=self.cfn_content_sha1,
                                 cf_input_parameters_sha1=self.cfn_input_param_sha1)
        dedicated = MagicMock()
        dedicated.configure_mock(cf_stack_index=1,
                                 type=ResourceModel.ResourceType.DEDICATED.name,
                                 status=ResourceModel.Status.LEASED.name,
                                 cf_template_sha1=self.cfn_content_sha1,
                                 cf_input_parameters_sha1=self.cfn_input_param_sha1)
        shared = MagicMock()
        shared.configure_mock(cf_stack_index=1,
                              type=ResourceModel.ResourceType.SHARED.name,
                              status=ResourceModel.Status.AVAILABLE.name,
                              cf_template_sha1=self.cfn_content_sha1,
                              cf_input_parameters_sha1=self.cfn_input_param_sha1)
        assume_role = MagicMock()
        assume_role.configure_mock(cf_stack_index=1,
                                   type=ResourceModel.ResourceType.ASSUME_ROLE.name,
                                   status=ResourceModel.Status.AVAILABLE.name,
                                   cf_template_sha1=self.cfn_content_sha1,
                                   cf_input_parameters_sha1=self.cfn_input_param_sha1)

        self.rm.cfn_templates['on_demand_template'] = {ResourcePool.CFN_RESOURCE_PARAM: on_demand}
        self.rm.cfn_templates['dedicated_template'] = {ResourcePool.CFN_RESOURCE_PARAM: dedicated}
        self.rm.cfn_templates['shared_template'] = {ResourcePool.CFN_RESOURCE_PARAM: shared}
        self.rm.cfn_templates['assume_role_template'] = {ResourcePool.CFN_RESOURCE_PARAM: assume_role}

        self.rm.release_resources()

        self.assertEqual(ResourceModel.Status.AVAILABLE.name, on_demand.status)
        self.assertEqual(ResourceModel.Status.DELETED.name, dedicated.status)
        self.assertEqual(ResourceModel.Status.AVAILABLE.name, shared.status)
        self.assertEqual(ResourceModel.Status.AVAILABLE.name, assume_role.status)

        self.assertEqual(ResourceModel.Status.AVAILABLE.name, on_demand.status)
        self.assertEqual(ResourceModel.Status.DELETED.name, dedicated.status)
        self.assertEqual(ResourceModel.Status.AVAILABLE.name, shared.status)
        self.assertEqual(ResourceModel.Status.AVAILABLE.name, assume_role.status)

        self.cfn_helper_mock.delete_cf_stack.assert_called_once()