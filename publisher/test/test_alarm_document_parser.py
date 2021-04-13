import unittest
import pytest
import os

from publisher.src.alarm_document_parser import AlarmDocumentParser

@pytest.mark.unit_test
class TestPublishDocuments(unittest.TestCase):
  def test_get_alarm_document_directory_with_valid_reference(self):
    expected = '../../documents/compute/alarm/asg-cpu-util/2020-07-13'
    local_dir = os.path.dirname(os.path.abspath(__file__))
    res = AlarmDocumentParser.get_document_directory('compute:alarm:asg-cpu-util:2020-07-13')
    assert os.path.relpath(res, local_dir) == expected

  def test_get_alarm_document_file_with_valid_reference(self):
    expected = '../../documents/compute/alarm/asg-cpu-util/2020-07-13/Documents/AlarmTemplate.yml'
    local_dir = os.path.dirname(os.path.abspath(__file__))
    res = AlarmDocumentParser.get_document_file('compute:alarm:asg-cpu-util:2020-07-13')
    assert os.path.relpath(res, local_dir) == expected

  def test_get_alarm_document_file_with_invalid_reference(self):
    with pytest.raises(Exception) as ex:
      AlarmDocumentParser.get_document_file('compute:alarm:does-not-exist:2020-07-13')
    assert "Failed to load metadata" in str(ex)

  def test_alarm_document_variable_parsing_valid(self):
    #Simple Example
    assert AlarmDocumentParser("""
      AlarmDescription:
        Fn::Join: [ '', [ 'Alarm by Digito that reports when autoscale group CPU utilization is over ', ${Thres hold}, '%' ] ]
      AlarmName: ${AlarmName}    
    """).get_variables() == set(["Thres hold", "AlarmName"])

    #No Variables
    assert AlarmDocumentParser("""
      AlarmDescription:
        Fn::Join: [ '', [ 'Alarm by Digito that reports when autoscale group CPU utilization is over ', 1, '%' ] ]
      AlarmName: Fixed name  
    """).get_variables() == set([])

    #Repeated Variables
    assert AlarmDocumentParser("""
      AlarmDescription:
        Fn::Join: [ '', [ 'Alarm by Digito that reports when autoscale group CPU utilization is over ', ${Threshold}, '%' ] ]
      AlarmName: Fn::Join: [ '', [${AlarmName} , 'with ', ${Threshold}] ]    
    """).get_variables() == set(["Threshold", "AlarmName"])

    #Same Line
    assert AlarmDocumentParser("AlarmName: Fn::Join: [ '', [${AlarmName2} , 'with ', ${Threshold2}] ]").get_variables() == set(["Threshold2", "AlarmName2"])

  def test_alarm_document_variable_parsing_invalid(self):
    #Invalid expressions
    assert AlarmDocumentParser("""AlarmName: Fn::Join: [ '', [${}, 'with ', {Threshold2}] ${]""").get_variables() == set([])

  def test_alarm_document_reference_id_ctor(self):
    under_test = AlarmDocumentParser.from_reference_id('compute:alarm:asg-cpu-util:2020-07-13')
    assert under_test.get_variables() == set(["AlarmName","Threshold","AutoScalingGroupName"])

  def test_alarm_document_replace_variables(self):
    under_test = AlarmDocumentParser("AlarmName: Fn::Join: [ '', [${AlarmName} , 'with ', ${Threshold}, ${Threshold}] ]")
    assert under_test\
      .replace_variables(AlarmName = "TestName", Threshold = 1)\
      .get_content() == "AlarmName: Fn::Join: [ '', [TestName , 'with ', 1, 1] ]"
