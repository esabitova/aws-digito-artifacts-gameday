import unittest
import pytest
import resource_manager.src.util.param_utils as param_utils
from resource_manager.src.resource_model import ResourceModel


@pytest.mark.unit_test
class TestParamUtils(unittest.TestCase):

    def test_parse_param_value_cache_success(self):
        cache = {'param1': {'param2': 'cache_value'}}
        cf_output = {'param1': {'param2': 'cache_value'}}
        containers = {'cache': cache, 'cf_output': cf_output}
        param_val_ref = '{{cache:param1>param2}}'
        actual_value = param_utils.parse_param_value(param_val_ref, containers)
        expected_value = cache['param1']['param2']
        self.assertEqual(actual_value, expected_value)

    def test_parse_param_value_cfn_output_success(self):
        cache = {'param1': {'param2': 'cache_value'}}
        cf_output = {'param1': {'param2': 'cache_value'}}
        containers = {'cache': cache, 'cf_output': cf_output}
        param_val_ref = '{{cf_output:param1>param2}}'
        actual_value = param_utils.parse_param_value(param_val_ref, containers)
        expected_value = cf_output['param1']['param2']
        self.assertEqual(actual_value, expected_value)

    def test_parse_param_value_not_supported_container_fail(self):
        cache = {'param1': {'param2': 'cache_value'}}
        cf_output = {'param1': {'param2': 'cache_value'}}
        containers = {'cache': cache, 'cf_output': cf_output}
        param_val_ref = '{{not-supported:param1>param2}}'
        self.assertRaises(Exception, param_utils.parse_param_value, param_val_ref, containers)

    def test_parse_param_value_invalid_format_fail(self):
        cache = {'param1': {'param2': 'cache_value'}}
        cf_output = {'param1': {'param2': 'cache_value'}}
        containers = {'cache': cache, 'cf_output': cf_output}
        param_val_ref = '{{cache}}'
        self.assertRaises(Exception, param_utils.parse_param_value, param_val_ref, containers)

    def test_parse_param_value_invalid_param_fail(self):
        cache = {'param1': {'param2': 'cache_value'}}
        cf_output = {'param1': {'param2': 'cache_value'}}
        containers = {'cache': cache, 'cf_output': cf_output}
        param_val_ref = '{{cache:aaaa}}'
        self.assertRaises(Exception, param_utils.parse_param_value, param_val_ref, containers)

    def test_parse_param_value_invalid_param_format_fail(self):
        cache = {'param1': {'param2': 'cache_value'}}
        cf_output = {'param1': {'param2': 'cache_value'}}
        containers = {'cache': cache, 'cf_output': cf_output}
        param_val_ref = '{{cache:param1:param2}}'
        self.assertRaises(Exception, param_utils.parse_param_value, param_val_ref, containers)

    def test_parse_param_value_simple_value_success(self):
        cache = {'param1': {'param2': 'cache_value'}}
        cf_output = {'param1': {'param2': 'cache_value'}}
        containers = {'cache': cache, 'cf_output': cf_output}
        expected_value = 'simple_value'
        actual_value = param_utils.parse_param_value(expected_value, containers)
        self.assertEqual(expected_value, actual_value)

    def test_parse_pool_size_success(self):
        actual_pool_size = param_utils.parse_pool_size('TemplateA={ON_DEMAND:1,DEDICATED:4},'
                                                       'TemplateB={ON_DEMAND:2,DEDICATED:2},'
                                                       'TemplateC={ON_DEMAND:3},'
                                                       'S3TemplateC={ON_DEMAND:4,DEDICATED:12}')

        expected_pool_size = dict(TemplateA={ResourceModel.Type.ON_DEMAND: 1, ResourceModel.Type.DEDICATED: 4},
                                  TemplateB={ResourceModel.Type.ON_DEMAND: 2, ResourceModel.Type.DEDICATED: 2},
                                  TemplateC={ResourceModel.Type.ON_DEMAND: 3},
                                  S3TemplateC={ResourceModel.Type.ON_DEMAND: 4, ResourceModel.Type.DEDICATED: 12})
        self.assertEqual(actual_pool_size, expected_pool_size)

    def test_parse_pool_size_bad_number_fail(self):
        self.assertRaises(Exception, param_utils.parse_pool_size, 'TemplateA={ON_DEMAND:1,DEDICATED:4},'
                                                                  'TemplateB={ON_DEMAND:1,DEDICATED:4},'
                                                                  'TemplateC={DEDICATED:B},'
                                                                  'S3TemplateC={ON_DEMAND:1,DEDICATED:4}')

    def test_parse_pool_size_extra_space_fail(self):
        self.assertRaises(Exception, param_utils.parse_pool_size, 'TemplateA={ON_DEMAND:1,DEDICATED:4},'
                                                                  'TemplateB={ON_DEMAND:1,DEDICATED:4},'
                                                                  ' TemplateC={DEDICATED:3},'
                                                                  'S3TemplateC={ON_DEMAND:1,DEDICATED:4}')

    def test_parse_pool_size_bad_char_fail(self):
        self.assertRaises(Exception, param_utils.parse_pool_size, 'TemplateA={ON_DEMAND:1,DEDICATED:4},'
                                                                  '?TemplateB={ON_DEMAND:1,DEDICATED:4},'
                                                                  'TemplateC={DEDICATED:3},'
                                                                  'S3TemplateC={ON_DEMAND:1,DEDICATED:4}')

    def test_parse_cfn_output_val_ref_success(self):
        cfn_template_name, cfn_output_name = \
            param_utils.parse_cfn_output_val_ref('{{cfn-output:RdsAuroraFailoverTestTemplate>ClusterId}}')
        self.assertEqual('RdsAuroraFailoverTestTemplate', cfn_template_name)
        self.assertEqual('ClusterId', cfn_output_name)

    def test_parse_cfn_output_val_ref_fail_1(self):
        self.assertRaises(Exception, param_utils.parse_cfn_output_val_ref, '{{a:RdsAuroraFailoverTestTemplate}}')

    def test_parse_cfn_output_val_ref_fail_2(self):
        self.assertRaises(Exception, param_utils.parse_cfn_output_val_ref,
                          '{{cfn-output:RdsAuroraFailoverTestTemplate}}')
