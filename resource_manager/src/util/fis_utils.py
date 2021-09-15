import logging

from boto3 import Session
from resource_manager.src.util.boto3_client_factory import client

logger = logging.getLogger(__name__)


def get_number_of_templates_with_tag(session: Session, template_tag: str) -> int:
    fis_client = client('fis', session)
    amount_of_templates = len([x for x in fis_client.list_experiment_templates()['experimentTemplates']
                               if x['tags'].get('Digito') == template_tag])
    return amount_of_templates
