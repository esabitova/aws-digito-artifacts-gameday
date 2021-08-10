import unittest
import pytest
import re
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from resource_manager.src.alarm_manager import AlarmManager, _resolve_yaml_reference
from publisher.src.alarm_document_parser import AlarmDocumentParser
import resource_manager.src.util.boto3_client_factory as client_factory

single_alarm_doc = """
AWSTemplateFormatVersion: '2010-09-09'
Parameters:
  SNSTopicARN:
    Type: String
Resources:
  ${AlarmLogicalId}:
    Type: 'AWS::CloudWatch::Alarm'
    Properties:
      AlarmActions:
        - Ref: SNSTopicARN
      AlarmDescription:
        Fn::Join: [ '', [ 'Alarm by Digito that reports when over time an ASG has many unhealthy hosts' ] ]
      AlarmName: ${AlarmName}
      ComparisonOperator: GreaterThanThreshold
      EvaluationPeriods: 180
      DatapointsToAlarm: 30
      Dimensions:
        - Name: TargetGroup
          Value: 'test_target_group'
        - Name: LoadBalancer
          Value: 'load_balancer'
      MetricName: UnHealthyHostCount
      Namespace: AWS/ApplicationELB
      Period: 60
      Statistic: Maximum
      Threshold: ${Threshold}
      TreatMissingData: missing
"""

analytics_alarm_doc = """
AWSTemplateFormatVersion: '2010-09-09'
Parameters:
  SNSTopicARN:
    Type: String
Resources:
  ${AlarmLogicalId}:
    Type: 'AWS::CloudWatch::Alarm'
    Properties:
      AlarmActions:
        - Ref: SNSTopicARN
      AlarmDescription:
        Fn::Join: [ '', [ 'Alarm by Digito that reports when volume write  is anomalous with band width ' ] ]
      AlarmName: ${AlarmName}
      ComparisonOperator: LessThanLowerOrGreaterThanUpperThreshold
      DatapointsToAlarm: 3
      EvaluationPeriods: 3
      Metrics:
        - Expression:
            Fn::Join: [ '', [ 'ANOMALY_DETECTION_BAND(m1,', ${Threshold}, ')' ] ]
          Id: ad1
        - Id: m1
          MetricStat:
            Metric:
              MetricName: VolumeWriteBytes
              Namespace: AWS/EC2
              Dimensions:
                - Name: VolumeId
                  Value: s-name-of-vol
            Period: 300
            Stat: Sum
      ThresholdMetricId: ad1
      TreatMissingData: missing
"""


@pytest.mark.unit_test
class TestAlarmManager(unittest.TestCase):

    def setUp(self):
        self.unique_prefix = "aaa"
        self.session_mock = MagicMock()
        self.cw_client_mock = MagicMock()
        self.cfn_helper_mock = MagicMock()
        self.s3_helper_mock = MagicMock()
        self.datetime_helper_mock = MagicMock()
        self.s3_helper_mock.upload_file.return_value = "s3://dummy-url"

        # Return the mock cw client when requested
        self.session_mock.client.side_effect = lambda service_name, config=None: ({
            'cloudwatch': self.cw_client_mock
        }).get(service_name)

        self.alarm_manager = AlarmManager(self.unique_prefix, self.session_mock,
                                          self.cfn_helper_mock, self.s3_helper_mock,
                                          self.datetime_helper_mock)

    def tearDown(self):
        # Clean client factory cache after each test.
        client_factory.clients = {}
        client_factory.resources = {}

    @patch('resource_manager.src.alarm_manager.AlarmDocumentParser.from_reference_id')
    def test_deploy_alarm_success(self, mock_dock_parser):
        self.cfn_helper_mock.describe_cf_stack.return_value = {
            'StackStatus': 'CREATE_COMPLETE'
        }
        mock_dock_parser.return_value = AlarmDocumentParser(single_alarm_doc)
        self.alarm_manager.deploy_alarm("service:alarm:single_alarm_doc:ver", {"Threshold": 1,
                                                                               "alarmId": "test_alarm",
                                                                               "SNSTopicARN": "topic"})

        self.s3_helper_mock.upload_file.assert_called_once()
        self.cfn_helper_mock.deploy_cf_stack.assert_called_once()
        self.cfn_helper_mock.describe_cf_stack.assert_called_once()

        assert self.alarm_manager.get_deployed_alarms() == {
            "test_alarm": {"AlarmName": f"single-alarm-doc-{self.unique_prefix}-0"}}

    @patch('resource_manager.src.alarm_manager.AlarmDocumentParser.from_reference_id')
    def test_deploy_alarm_failure_cfn(self, mock_dock_parser):
        self.cfn_helper_mock.describe_cf_stack.return_value = {
            'StackStatus': 'ROLLBACK_COMPLETE'
        }
        self.cfn_helper_mock.describe_cf_stack_events.return_value = [
            {"LogicalResourceId": "res1", "ResourceStatus": "CREATE_COMPLETE"},
            {"LogicalResourceId": "res2", "ResourceStatus": "CREATE_FAILED",
             "ResourceStatusReason": "Internal_Failure_Reason"}

        ]

        mock_dock_parser.return_value = AlarmDocumentParser(single_alarm_doc)
        with pytest.raises(Exception) as err:
            self.alarm_manager.deploy_alarm("service:alarm:single_alarm_doc:ver", {"Threshold": 1,
                                                                                   "SNSTopicARN": "topic"})

        assert "Failed to deploy alarm " in str(err)
        assert "Internal_Failure_Reason" in str(err)

    @patch('resource_manager.src.alarm_manager.AlarmDocumentParser.from_reference_id')
    def test_deploy_alarm_failure_missing_variables(self, mock_dock_parser):
        self.cfn_helper_mock.describe_cf_stack.return_value = {
            'StackStatus': 'ROLLBACK_COMPLETE'
        }
        self.cfn_helper_mock.describe_cf_stack_events.return_value = [
            {"LogicalResourceId": "res1", "ResourceStatus": "CREATE_COMPLETE"},
            {"LogicalResourceId": "res2", "ResourceStatus": "CREATE_FAILED",
             "ResourceStatusReason": "Internal_Failure_Reason"}

        ]

        mock_dock_parser.return_value = AlarmDocumentParser(single_alarm_doc)
        with pytest.raises(Exception) as err:
            self.alarm_manager.deploy_alarm("service:alarm:single_alarm_doc:ver", {})

        assert "Test must provide values to the following variables" in str(err)
        assert "Threshold" in str(err)

    @patch('resource_manager.src.alarm_manager.AlarmDocumentParser.from_reference_id')
    def test_destroy_deployed_alarms(self, mock_dock_parser):
        self.cfn_helper_mock.describe_cf_stack.return_value = {
            'StackStatus': 'CREATE_COMPLETE'
        }
        mock_dock_parser.return_value = AlarmDocumentParser(single_alarm_doc)
        self.alarm_manager.deploy_alarm("service:alarm:single_alarm_doc:ver", {"Threshold": 1,
                                                                               "alarmId": "test_alarm",
                                                                               "SNSTopicARN": "topic"})

        self.alarm_manager.destroy_deployed_alarms()
        self.cfn_helper_mock.delete_cf_stack.assert_called_once()

    @patch('resource_manager.src.alarm_manager.AlarmDocumentParser.from_reference_id')
    def test_destroy_deployed_multiple_alarms(self, mock_dock_parser):
        self.cfn_helper_mock.describe_cf_stack.return_value = {
            'StackStatus': 'CREATE_COMPLETE'
        }
        mock_dock_parser.side_effect = [AlarmDocumentParser(single_alarm_doc), AlarmDocumentParser(analytics_alarm_doc)]
        self.alarm_manager.deploy_alarm("service:alarm:single_alarm_doc:ver", {"Threshold": 1,
                                                                               "SNSTopicARN": "topic"})
        self.alarm_manager.deploy_alarm("service:alarm:analytics_alarm_doc:ver", {"Threshold": 1,
                                                                                  "SNSTopicARN": "topic"})

        assert self.alarm_manager.get_deployed_alarms() == {
            "alarm-0": {"AlarmName": f"single-alarm-doc-{self.unique_prefix}-0"},
            "alarm-1": {"AlarmName": f"analytics-alarm-doc-{self.unique_prefix}-1"}
        }

        self.alarm_manager.destroy_deployed_alarms()
        assert self.cfn_helper_mock.delete_cf_stack.call_count == 2

    @patch('resource_manager.src.alarm_manager.AlarmDocumentParser.from_reference_id')
    def test_collect_alarms_without_data_all_have_data(self, mock_dock_parser):
        self.cfn_helper_mock.describe_cf_stack.return_value = {
            'StackStatus': 'CREATE_COMPLETE'
        }
        mock_dock_parser.side_effect = [AlarmDocumentParser(single_alarm_doc), AlarmDocumentParser(analytics_alarm_doc)]
        self.alarm_manager.deploy_alarm("service:alarm:single_alarm_doc:ver", {"Threshold": 1,
                                                                               "SNSTopicARN": "topic"})
        self.alarm_manager.deploy_alarm("service:alarm:analytics_alarm_doc:ver", {"Threshold": 1,
                                                                                  "SNSTopicARN": "topic"})

        self.cw_client_mock.get_metric_statistics.side_effect = lambda **request: ({
            'AWS/EC2': {"Datapoints": [{"Timestamp": "2020", "SampleCount": 4}]},
            'AWS/ApplicationELB': {"Datapoints": [{"Timestamp": "2020", "SampleCount": 4}]},
        }).get(request.get("Namespace"))
        missing_data = self.alarm_manager.collect_alarms_without_data(300)

        assert missing_data == {}

    @patch('resource_manager.src.alarm_manager.AlarmDocumentParser.from_reference_id')
    def test_collect_alarms_without_data_some_dont_have_data(self, mock_dock_parser):
        self.cfn_helper_mock.describe_cf_stack.return_value = {
            'StackStatus': 'CREATE_COMPLETE'
        }
        mock_dock_parser.side_effect = [AlarmDocumentParser(single_alarm_doc), AlarmDocumentParser(analytics_alarm_doc)]
        self.alarm_manager.deploy_alarm("service:alarm:single_alarm_doc:ver", {"Threshold": 1,
                                                                               "alarmId": "no-data",
                                                                               "SNSTopicARN": "topic"})
        self.alarm_manager.deploy_alarm("service:alarm:analytics_alarm_doc:ver", {"Threshold": 1,
                                                                                  "alarmId": "has-data",
                                                                                  "SNSTopicARN": "topic"})
        self.datetime_helper_mock.utcnow.side_effect = [
            # Mock timestamps for the call below
            datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            datetime(2020, 1, 1, 0, 1, 0, tzinfo=timezone.utc),
            datetime(2020, 1, 1, 1, 0, 0, tzinfo=timezone.utc),
        ]
        self.cw_client_mock.get_metric_statistics.side_effect = lambda **request: ({
            'AWS/EC2': {"Datapoints": [{"Timestamp": "2020", "SampleCount": 4}]},
            'AWS/ApplicationELB': {"Datapoints": []},
        }).get(request.get("Namespace"))

        # Test:
        missing_data = self.alarm_manager.collect_alarms_without_data(300)
        alarm_logical_id = re.sub("-", "0", f'single-alarm-doc-{self.unique_prefix}-0')
        assert list(missing_data.keys()) == ['no-data']
        assert missing_data['no-data'][alarm_logical_id]['metric_namespace'] == "AWS/ApplicationELB"

    @patch('resource_manager.src.alarm_manager.AlarmDocumentParser.from_reference_id')
    def test_collect_alarms_without_data_failure(self, mock_dock_parser):
        self.cfn_helper_mock.describe_cf_stack.return_value = {
            'StackStatus': 'CREATE_COMPLETE'
        }
        no_metric_alarm = """
    AWSTemplateFormatVersion: '2010-09-09'
    Resources:
      VolumeWriteBytesAlarm:
        Type: 'AWS::CloudWatch::Alarm'
        Properties:
          AlarmActions:
            - Ref: SNSTopicARN
          AlarmDescription:
            Fn::Join: [ '', [ 'Alarm by Digito that reports when volume write throughput is  ', 1 ] ]
          AlarmName: analytics_alarm_doc_unique_name
          ComparisonOperator: LessThanLowerOrGreaterThanUpperThreshold
          DatapointsToAlarm: 3
          EvaluationPeriods: 3
          Metrics:
            - Expression:
                Fn::Join: [ '', [ 'ANOMALY_DETECTION_BAND(m1,', 1, ')' ] ]
              Id: ad1
    """
        mock_dock_parser.return_value = AlarmDocumentParser(no_metric_alarm)
        self.alarm_manager.deploy_alarm("service:alarm:no_metric_alarm:ver", {})

        with pytest.raises(Exception) as err:
            self.alarm_manager.collect_alarms_without_data(300)

        assert "contained no metrics" in str(err)

    def test_replace_yaml_reference_noop_primitive(self):
        self.assertTrue(_resolve_yaml_reference("string", {}), "string")
        self.assertTrue(_resolve_yaml_reference(12345, {}), 12345)

    def test_replace_yaml_reference_noop_unexpected(self):
        self.assertTrue(_resolve_yaml_reference({"weird": "value"}, {}), {"weird": "value"})
        self.assertTrue(_resolve_yaml_reference({"Ref": "param1", "weird": "value"}, {}),
                        {"Ref": "param1", "weird": "value"})

    def test_replace_yaml_reference_replace_ref(self):
        self.assertTrue(_resolve_yaml_reference({"Ref": "param1"}, {"param1": "value"}), "value")

    def test_replace_yaml_reference_fails_if_missing(self):
        with pytest.raises(ValueError) as err:
            self.assertTrue(_resolve_yaml_reference({"Ref": "param1"}, {}))
        assert "Failed to Replace Ref" in str(err)
