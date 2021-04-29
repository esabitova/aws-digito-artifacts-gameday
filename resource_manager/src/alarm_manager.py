import logging
import re
from datetime import timedelta, datetime
from concurrent.futures import ThreadPoolExecutor
from cfn_tools import load_yaml
from .util.cw_util import get_cw_metric_statistics


class AlarmManager:
    """
    helper class to deploy alarms during tests. Tracks all alarms deployed during
    a test and cleans them as soon as the test completes
    """

    def __init__(self, unique_suffix, boto3_session, cfn_helper, s3_helper, datetime_helper=datetime):
        self.unique_suffix = unique_suffix
        self.session = boto3_session
        self.cfn_helper = cfn_helper
        self.s3_helper = s3_helper
        # datetime_helper just datetime but allows tests to replace the provider
        self.datetime_helper = datetime_helper
        self.deployed_stacks = {}

    def deploy_alarm(self, name, raw, cfn_input_params):
        content = load_yaml(raw)
        stack_name = f'{re.sub(r"[^-a-zA-Z0-9]","-",name)}-{self.unique_suffix}'
        s3_url = self.s3_helper.upload_file(f'alarm_templates/{name}.yml', content)
        self.deployed_stacks[stack_name] = content
        self.cfn_helper.deploy_cf_stack(s3_url,
                                        stack_name,
                                        **cfn_input_params)
        # Verify Stack Was deployed Successfully
        status = self.cfn_helper.describe_cf_stack(stack_name)['StackStatus']
        expected_statuses = ['CREATE_COMPLETE', 'UPDATE_COMPLETE']
        if status not in expected_statuses:
            failures = "\n  ".join([f"LogicalResourceId {i['LogicalResourceId']} : {i['ResourceStatusReason']}"
                                    for i in self.cfn_helper.describe_cf_stack_events(stack_name)
                                    if "FAILED" in i['ResourceStatus']
                                    ])
            raise Exception(f'Unexpected Status for deployed alarm {stack_name}\n'
                            f'template {s3_url}\n'
                            f'Status is {status} expected one of {expected_statuses}\n'
                            f'Failures:\n  {failures}\n')

    def destroy_deployed_alarms(self):
        logging.info(f"Destroying [{len(self.deployed_stacks)}] alarms stacks.")
        with ThreadPoolExecutor(max_workers=10) as t_executor:
            for alarm_stack in self.deployed_stacks.keys():
                t_executor.submit(self._destroy_single_alarm, alarm_stack)

    def _destroy_single_alarm(self, alarm_stack):
        logging.info(f"Destroying [{alarm_stack}] alarm_stack.")
        self.cfn_helper.delete_cf_stack(alarm_stack)

    def collect_alarms_without_data(self):
        """
        Verifies that all alarm metrics have data on the requested dimension
        Returns list of alarms that do not report data
        """
        alarms_without_data = {
            alarm: self._collect_alarms_without_data(alarm)
            for alarm in self.deployed_stacks.keys()
        }
        return {alarm: missing_metrics
                for alarm, missing_metrics in alarms_without_data.items()
                if len(missing_metrics) > 0
                }

    def _collect_alarms_without_data(self, alarm_name):
        # iterate over Resources of type Alarm AWS::CloudWatch::Alarm
        alarm = self.deployed_stacks[alarm_name]
        metrics = {}
        metrics_without_data = {}
        for res_name, resource in alarm['Resources'].items():
            if not resource['Type'] == 'AWS::CloudWatch::Alarm':
                continue
            # Collect from Metrics
            if 'Metrics' in resource['Properties']:
                for metric in resource['Properties']['Metrics']:
                    if 'MetricStat' in metric:
                        metric_props = metric['MetricStat']
                        metrics[f'{res_name}/{metric["Id"]}'] = {
                            'metric_namespace': metric_props['Metric']['Namespace'],
                            'metric_name': metric_props['Metric']['MetricName'],
                            'metric_dimensions': {
                                i['Name']: i['Value']
                                for i in metric_props['Metric'].get('Dimensions', [])
                            },
                            'period': metric_props['Period'],
                            'statistics': ['SampleCount']
                        }
            else:
                metric_props = resource['Properties']
                metrics[res_name] = {
                    'metric_namespace': metric_props['Namespace'],
                    'metric_name': metric_props['MetricName'],
                    'metric_dimensions': {
                        i['Name']: i['Value']
                        for i in metric_props.get('Dimensions', [])
                    },
                    'period': metric_props['Period'],
                    'statistics': ['SampleCount']
                }

        if not metrics:
            raise Exception(f"Document {alarm_name} contained no alarms (Alarm AWS::CloudWatch::Alarm)")

        end_time_utc = self.datetime_helper.utcnow()
        for metric_name, metric_props in metrics.items():
            start_time_utc = self.datetime_helper.utcnow() - timedelta(seconds=metric_props['period'] * 3)
            data_points = get_cw_metric_statistics(self.session, start_time_utc, end_time_utc, **metric_props)
            if not data_points:
                metrics_without_data[metric_name] = metric_props
        return metrics_without_data
