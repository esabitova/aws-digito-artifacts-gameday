"""
A helper class for alarm documents. Looks up alarm from referenceId.
Gets search_replace parameters in alarm document, and gives
"""
from __future__ import annotations

import json
import os
import re


def read_metadata(directory):
  try:
    file_path = os.path.join(directory,'Documents/metadata.json')
    with open(file_path) as metadata_file:
      return json.load(metadata_file)
  except Exception as e:
    raise Exception('Failed to load metadata %s', file_path, e)

class AlarmDocumentParser:

  _pattern = re.compile(r"\$\{([^}]+)\}")

  def __init__(self, alarm_document_content):
    self._alarm_document_content = alarm_document_content

  def get_content(self):
    return self._alarm_document_content

  def get_variables(self):
    """
    collect all elements such as ${Threshold} from the file and returns as a
    unique set of values
    """
    return set(
        ( m.group(1)
          for m in
          AlarmDocumentParser._pattern.finditer(self._alarm_document_content) )
    )

  def replace_variables(self, **variables):
    """
    accepts a dictionary of variable values to replace in the document
    """
    doc = self._alarm_document_content
    for var_name, var_value in variables.items():
      doc = doc.replace("${%s}" % str(var_name), str(var_value))
    return AlarmDocumentParser(doc)

  @staticmethod
  def from_reference_id(reference_id):
    file_path = AlarmDocumentParser.get_document_file(reference_id)
    with open(file_path) as f:
      return AlarmDocumentParser(f.read())

  @staticmethod
  def get_document_directory(reference_id):
    local_dir = os.path.dirname(os.path.abspath(__file__))
    elements = reference_id.split(':')
    return os.path.join(local_dir, '../../documents',  *elements)

  @staticmethod
  def get_document_file(reference_id):
    file_path = AlarmDocumentParser.get_document_directory(reference_id)
    file_name = read_metadata(file_path)['alarmContentPath']
    return os.path.join(file_path, 'Documents', file_name)