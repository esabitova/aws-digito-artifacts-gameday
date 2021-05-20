import logging
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta, datetime

from cfn_tools import load_yaml

from .util.cw_util import get_cw_metric_statistics
from publisher.src.alarm_document_parser import AlarmDocumentParser


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
        self.deployed_alarms = {}

    def deploy_alarm(self, alarm_reference_id, input_params):

        alarm_name = alarm_reference_id.split(':')[2]
        # Name for the alarm is either set by the user or generated as alarm-0 for first alarm etc.
        alarm_id = input_params.pop('alarmId', f'alarm-{len(self.deployed_alarms)}')

        unique_alarm_suffix = f'{self.unique_suffix}-{len(self.deployed_alarms)}'

        unique_alarm_name = f'{_remove_special_characters(alarm_name)}-{unique_alarm_suffix}'
        input_params['AlarmName'] = unique_alarm_name
        input_params['AlarmLogicalId'] = _legal_cfn_resource_id(unique_alarm_name)

        # Replace ${Variable} to convert the Document to a valid Cfn Template
        raw_alarm_document = AlarmDocumentParser.from_reference_id(alarm_reference_id)
        variables = raw_alarm_document.get_variables()
        alarm_document = raw_alarm_document.replace_variables(**input_params)

        if alarm_document.get_variables():
            raise Exception(f'Test must provide values to the following variables: '
                            f'{str(list(alarm_document.get_variables()))}'
                            f'referenceId: {alarm_reference_id}'
                            f'path: {AlarmDocumentParser.get_document_directory(alarm_reference_id)}')

        # Use the remaining parameters to build the alarm as a Cfn Template
        cfn_parameters = {k: v for k, v in input_params.items() if k not in variables}
        content = load_yaml(alarm_document.get_content())
        s3_url = self.s3_helper.upload_file(f'alarm_templates/{alarm_name}.yml', content)
        self.deployed_alarms[alarm_id] = {
            "alarm_name": unique_alarm_name,
            "content": content
        }

        # Todo verify Cfn param and provide better error messages before deploying
        self.cfn_helper.deploy_cf_stack(s3_url,
                                        unique_alarm_name,
                                        **cfn_parameters)
        # Verify Stack Was deployed Successfully
        status = self.cfn_helper.describe_cf_stack(unique_alarm_name)['StackStatus']
        expected_statuses = ['CREATE_COMPLETE', 'UPDATE_COMPLETE']
        if status not in expected_statuses:
            failures = "\n  ".join([f"LogicalResourceId {i['LogicalResourceId']} : {i['ResourceStatusReason']}"
                                    for i in self.cfn_helper.describe_cf_stack_events(unique_alarm_name)
                                    if "FAILED" in i['ResourceStatus']
                                    ])
            raise Exception(f'Failed to deploy alarm {alarm_id}: {unique_alarm_name}\n'
                            f'template {s3_url}\n'
                            f'Status is {status} expected one of {expected_statuses}\n'
                            f'Failures:\n  {failures}\n')

    def get_deployed_alarms(self):
        return {
            alarm_id: {"AlarmName": v["alarm_name"]} for alarm_id, v in self.deployed_alarms.items()
        }

    def destroy_deployed_alarms(self):
        logging.info(f"Destroying [{len(self.deployed_alarms)}] alarms stacks.")
        with ThreadPoolExecutor(max_workers=10) as t_executor:
            for alarm_id, v in self.deployed_alarms.items():
                t_executor.submit(self._destroy_single_alarm, alarm_id, v["alarm_name"])

    def _destroy_single_alarm(self, alarm_id, alarm_name):
        logging.info(f"Destroying [{alarm_id}] alarm_stack {alarm_name}.")
        self.cfn_helper.delete_cf_stack(alarm_name)

    def collect_alarms_without_data(self, data_period_seconds):
        """
        Verifies that all alarm metrics have data on the requested dimension
        Returns list of alarms that do not report data
        """
        alarms_without_data = {
            alarm: self._collect_alarms_without_data(alarm, data_period_seconds)
            for alarm in self.deployed_alarms.keys()
        }
        return {alarm: missing_metrics
                for alarm, missing_metrics in alarms_without_data.items()
                if len(missing_metrics) > 0
                }

    def _collect_alarms_without_data(self, alarm_id, data_period_seconds):
        # iterate over Resources of type Alarm AWS::CloudWatch::Alarm
        alarm = self.deployed_alarms[alarm_id]["content"]
        alarm_name = self.deployed_alarms[alarm_id]["alarm_name"]
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
            raise Exception(
                f"{alarm_id} Document {alarm_name} contained no metrics under (Alarm AWS::CloudWatch::Alarm)")

        end_time_utc = self.datetime_helper.utcnow()
        for metric_name, metric_props in metrics.items():
            start_time_utc = end_time_utc - timedelta(seconds=(metric_props['period'] + data_period_seconds))
            data_points = get_cw_metric_statistics(self.session, start_time_utc, end_time_utc, **metric_props)
            if not data_points:
                metrics_without_data[metric_name] = metric_props

        return metrics_without_data


def _remove_special_characters(str):
    return re.sub(r"[^-a-zA-Z0-9]", "-", str)


def _legal_cfn_resource_id(str):
    return re.sub("-", "0", str)
