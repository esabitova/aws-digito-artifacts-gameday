import json
import logging
import os
import urllib
import urllib.parse

import boto3
from pymongo import MongoClient

if len(logging.getLogger().handlers) > 0:
    # The Lambda environment pre-configures a handler logging to stderr. If a handler is already configured,
    # `.basicConfig` does not execute. Thus we set the level directly.
    logging.getLogger().setLevel(logging.INFO)
else:
    logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def handler(event, context):
    secret_id = os.environ.get('SECRET_ID')
    if secret_id is None:
        raise KeyError('Requires SECRET_ID in events')

    endpoint = os.environ.get('ENDPOINT')
    if endpoint is None:
        raise KeyError('Requires ENDPOINT in events')

    port = os.environ.get('PORT')
    if port is None:
        raise KeyError('Requires PORT in events')

    secretsmanager_client = boto3.client('secretsmanager')
    get_secret_value_response = secretsmanager_client.get_secret_value(SecretId=secret_id)
    secret = get_secret_value_response['SecretString']
    deserialized = json.loads(secret)
    username = urllib.parse.quote_plus(deserialized['username'])
    password = urllib.parse.quote_plus(deserialized['password'])
    client = None
    try:
        pem_file_abs_path = '/opt/python/rds-combined-ca-bundle.pem'
        client = MongoClient(f'mongodb://{username}:{password}@{endpoint}:{port}', ssl=True,
                             ssl_ca_certs=pem_file_abs_path, replicaSet="rs0", readPreference="secondaryPreferred",
                             retryWrites=False)
        logger.info(f'Trying to ping DocumentDb instance on endpoint={endpoint}, port={port}')
        response = client.db_name.command('ping')
        logger.info(f'Response from ping command is {response}')
    finally:
        if client is not None:
            client.close()
