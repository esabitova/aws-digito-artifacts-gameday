import unittest
import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone
from resource_manager.src.alarm_manager import AlarmManager
import resource_manager.src.util.boto3_client_factory as client_factory


single_alarm_doc = """
AWSTemplateFormatVersion: '2010-09-09'
Parameters:
  SNSTopicARN:
    Type: String
Resources:
  UnHealthyHostCountAlarm:
    Type: 'AWS::CloudWatch::Alarm'
    Properties:
      AlarmActions:
        - Ref: SNSTopicARN
      AlarmDescription:
        Fn::Join: [ '', [ 'Alarm by Digito that reports when over time an ASG has many unhealthy hosts' ] ]
      AlarmName: single_alarm_unique_name
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
      Threshold: 1
      TreatMissingData: missing
"""

analytics_alarm_doc = """
AWSTemplateFormatVersion: '2010-09-09'
Parameters:
  SNSTopicARN:
    Type: String
Resources:
  VolumeWriteBytes:
    Type: 'AWS::CloudWatch::Alarm'
    Properties:
      AlarmActions:
        - Ref: SNSTopicARN
      AlarmDescription:
        Fn::Join: [ '', [ 'Alarm by Digito that reports when volume write  is anomalous with band width ', 1 ] ]
      AlarmName: analytics_alarm_doc_unique_name
      ComparisonOperator: LessThanLowerOrGreaterThanUpperThreshold
      DatapointsToAlarm: 3
      EvaluationPeriods: 3
      Metrics:
        - Expression:
            Fn::Join: [ '', [ 'ANOMALY_DETECTION_BAND(m1,', 1, ')' ] ]
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

    def test_deploy_alarm_success(self):
        self.cfn_helper_mock.describe_cf_stack.return_value = {
            'StackStatus': 'CREATE_COMPLETE'
        }
        self.alarm_manager.deploy_alarm("single_alarm_doc", single_alarm_doc, {"SNSTopicARN": "topic"})

        self.s3_helper_mock.upload_file.assert_called_once()
        self.cfn_helper_mock.deploy_cf_stack.assert_called_once()
        self.cfn_helper_mock.describe_cf_stack.assert_called_once()

    def test_deploy_alarm_failure(self):
        self.cfn_helper_mock.describe_cf_stack.return_value = {
            'StackStatus': 'ROLLBACK_COMPLETE'
        }
        self.cfn_helper_mock.describe_cf_stack_events.return_value = [
            {"LogicalResourceId": "res1", "ResourceStatus": "CREATE_COMPLETE"},
            {"LogicalResourceId": "res2", "ResourceStatus": "CREATE_FAILED",
             "ResourceStatusReason": "Internal_Failure_Reason"}

        ]
        with pytest.raises(Exception) as err:
            self.alarm_manager.deploy_alarm("single_alarm_doc", single_alarm_doc, {"SNSTopicARN": "topic"})

        assert "Unexpected Status for deployed alarm " in str(err)
        assert "Internal_Failure_Reason" in str(err)

    def test_destroy_deployed_alarms(self):
        self.cfn_helper_mock.describe_cf_stack.return_value = {
            'StackStatus': 'CREATE_COMPLETE'
        }
        self.alarm_manager.deploy_alarm("single_alarm_doc", single_alarm_doc, {"SNSTopicARN": "topic"})

        self.alarm_manager.destroy_deployed_alarms()
        self.cfn_helper_mock.delete_cf_stack.assert_called_once()

    def test_destroy_deployed_multiple_alarms(self):
        self.cfn_helper_mock.describe_cf_stack.return_value = {
            'StackStatus': 'CREATE_COMPLETE'
        }
        self.alarm_manager.deploy_alarm("single_alarm_doc", single_alarm_doc, {"SNSTopicARN": "topic"})
        self.alarm_manager.deploy_alarm("analytics_alarm_doc", analytics_alarm_doc, {"SNSTopicARN": "topic"})

        self.alarm_manager.destroy_deployed_alarms()
        assert self.cfn_helper_mock.delete_cf_stack.call_count == 2

    def test_collect_alarms_without_data_all_have_data(self):
        self.cfn_helper_mock.describe_cf_stack.return_value = {
            'StackStatus': 'CREATE_COMPLETE'
        }
        self.alarm_manager.deploy_alarm("single_alarm_doc", single_alarm_doc, {"SNSTopicARN": "topic"})
        self.alarm_manager.deploy_alarm("analytics_alarm_doc", analytics_alarm_doc, {"SNSTopicARN": "topic"})

        self.cw_client_mock.get_metric_statistics.side_effect = lambda **request: ({
            'AWS/EC2': {"Datapoints": [{"Timestamp": "2020", "SampleCount": 4}]},
            'AWS/ApplicationELB': {"Datapoints": [{"Timestamp": "2020", "SampleCount": 4}]},
        }).get(request.get("Namespace"))
        missing_data = self.alarm_manager.collect_alarms_without_data()

        assert missing_data == {}

    def test_collect_alarms_without_data_some_dont_have_data(self):
        self.cfn_helper_mock.describe_cf_stack.return_value = {
            'StackStatus': 'CREATE_COMPLETE'
        }
        self.alarm_manager.deploy_alarm("single_alarm_doc", single_alarm_doc, {"SNSTopicARN": "topic"})
        self.alarm_manager.deploy_alarm("analytics_alarm_doc", analytics_alarm_doc, {"SNSTopicARN": "topic"})

        self.datetime_helper_mock.utcnow.side_effect = [
            # Mock timestamps for the call below
            datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            datetime(2020, 1, 1, 0, 0, 1, tzinfo=timezone.utc),
            datetime(2020, 1, 1, 0, 1, 0, tzinfo=timezone.utc),
            datetime(2020, 1, 1, 0, 1, 1, tzinfo=timezone.utc),
            datetime(2020, 1, 1, 1, 0, 0, tzinfo=timezone.utc),
        ]
        self.cw_client_mock.get_metric_statistics.side_effect = lambda **request: ({
            'AWS/EC2': {"Datapoints": [{"Timestamp": "2020", "SampleCount": 4}]},
            'AWS/ApplicationELB': {"Datapoints": []},
        }).get(request.get("Namespace"))
        expected_alarm_name = f'single-alarm-doc-{self.unique_prefix}'

        # Test:
        missing_data = self.alarm_manager.collect_alarms_without_data()
        assert list(missing_data.keys()) == [expected_alarm_name]
        assert missing_data[expected_alarm_name]['UnHealthyHostCountAlarm']['metric_namespace'] == "AWS/ApplicationELB"

    def test_collect_alarms_without_data_failure(self):
        self.cfn_helper_mock.describe_cf_stack.return_value = {
            'StackStatus': 'CREATE_COMPLETE'
        }
        no_metric_alarm = """
    AWSTemplateFormatVersion: '2010-09-09'
    Resources:
      AbnormalRequestPerTargetAnomalyDetector:
        Type: 'AWS::CloudWatch::AnomalyDetector'
        Properties:
          MetricName: RequestCountPerTarget
          Namespace: AWS/ApplicationELB
          Stat: Average
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
        self.alarm_manager.deploy_alarm("no_metric_alarm", no_metric_alarm, {})

        with pytest.raises(Exception) as err:
            self.alarm_manager.collect_alarms_without_data()

        assert "contained no alarms" in str(err)
