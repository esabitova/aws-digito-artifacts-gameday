import os
import json
import string
import concurrent.futures
import uuid
import random
from time import sleep
from copy import deepcopy

import psycopg2


CLUSTER_HOST = os.environ['REDSHIFT_CLUSTER_HOST']
DB_NAME = os.environ['REDSHIFT_DB']
DB_USER = os.environ['REDSHIFT_DB_USER']
DB_PASSWORD = os.environ['REDSHIFT_DB_PASSWORD']
global_config = {
    'host': CLUSTER_HOST,
    'cluster_id': CLUSTER_HOST.split('.')[0],
    'port': 5439,
    'dbname': DB_NAME,
    'user': DB_USER,
    'password': DB_PASSWORD,
    'number_of_threads': 20,
    'schema': "test-" + str(uuid.uuid4()),
    'users': {
        'real_amount': 5,
        'multiplier': 4,
        'group': "test_writers-" + str(uuid.uuid4())
    },
    'threads_delay_range_milliseconds': 10000,
    'number_of_columns': 500,
    'batch_size': 10,
    'huge_inserts': 2
}


capitals = string.ascii_uppercase
lowers = string.ascii_lowercase
letters = string.ascii_letters
digits = string.digits
translation_table = str.maketrans({a: None for a in """"'\/@"""})
special = string.punctuation.translate(translation_table)


def generate_username(length=10):
    """
    Generates username using random library
    :param length: length of random generated username
    :return: username
    """
    user = ''.join(random.choice(letters.lower()) for i in range(length))
    return user


def generate_password(length=12):
    """
    Generates password with defined length
    :param length: length of random generated password
    :return: password
    """
    if length < 10:
        return "length should be 10 symbols or more"
    password_letters = random.choice(capitals) + random.choice(lowers) + (
        ''.join(random.choice(letters) for i in range(length - (length // 2)))[2:]
    )
    password_digits = ''.join(random.choice(digits) for i in range((length - (length // 2)) // 2))
    password_special = ''.join(
        random.choice(special) for i in range(length - (len(password_letters + password_digits))))
    p = password_letters + str(password_digits) + password_special
    password = ''.join(random.sample(p, len(p)))
    return password


def create_users(config=None):
    """
    Connects to db defined in config and creates users which have access to schema described in config
    :param config: dictionary with configuration params
    :return: list of objects with user properties
    """
    users = [{'user': generate_username(), 'password': generate_password(), 'created': False, 'exception': None}
             for a in range(config['users']['real_amount'])]
    conn = psycopg2.connect(
        dbname=config['dbname'], host=config['host'], port=config['port'], user=config['user'],
        password=config['password']
    )
    schema = config['schema']
    group = "test_writers2-" + str(uuid.uuid4())
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(f"""create schema if not exists "{schema}";""")
                cur.execute(f"""create group "{group}";""")
                cur.execute(f"""grant all on all tables in schema "{schema}" to group "{group}";""")
                cur.execute(f"""grant all on schema "{schema}" to group "{group}";""")
                conn.commit()
                for user in users:
                    try:
                        cur.execute(f"""create user "{user['user']}" with password '{user['password']}'
                                        in group "{group}";""")
                        user['created'] = True
                    except Exception as e:
                        print(e)
                        user['created'] = False
                        user['exception'] = str(e.args)
                        conn.commit()
                    conn.commit()
                cur.close()
    finally:
        conn.close()
    return users


def batch_execution(user=None, config=None):
    """
    Connects to DB, creates table and executes batch queries
    :param user: dictionary with user properties
    :param config: dictionary with configuration params
    :return: dictionary with keys "user", "table"
    """
    sleep(random.randint(0, config['threads_delay_range_milliseconds']) / 1000)
    config = deepcopy(config)
    config['user'] = user['user']
    config['password'] = user['password']
    schema = config['schema']
    table = "test-" + str(uuid.uuid4())
    columns = [uuid.uuid4().hex for a in range(config['number_of_columns'])]
    table_sql = f"""create table if not exists
              "{config['dbname']}"."{schema}"."{table}"("{('" varchar, "'.join(columns) + '" varchar') })"""
    conn = psycopg2.connect(dbname=config['dbname'], host=config['host'],
                            port=config['port'], user=config['user'],
                            password=config['password'])
    str_values = "'" + ", '".join([str(uuid.uuid4()) + "'" for a in range(config['number_of_columns'])])
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(table_sql)
                conn.commit()
                cur.executemany(f"""insert into "{config['dbname']}"."{schema}"."{table}" ("{'", "'.join(columns)}")
                              values ({str_values})""", vars_list=[None] * config['batch_size'])
                cur.executemany(f"""insert into "{config['dbname']}"."{schema}"."{table}"
                                (select * from "{config['dbname']}"."{schema}"."{table}")""",
                                vars_list=[None] * config['huge_inserts'])
                conn.commit()
                cur.executemany(f"""select * from "{config['dbname']}"."{schema}"."{table}" """,
                                vars_list=[None] * config['batch_size'])
                cur.close()
    finally:
        conn.close()
    return {'user': user, 'table': f""" "{config['dbname']}"."{schema}"."{table}" """}


def concurrent_handler(func=None, config=None):
    """
    Executes in parallel several instances of function
    :param func: function name
    :param config: dictionary with configuration params
    :return: None
    """
    users = create_users(config)
    with concurrent.futures.ThreadPoolExecutor(max_workers=config['number_of_threads']) as executor:
        future_to_user = {executor.submit(func, user, config): user for user in users * config['users']['multiplier']}
        for future in concurrent.futures.as_completed(future_to_user):
            user = future_to_user[future]
            try:
                future.result()
            except Exception as exc:
                print('%r generated an exception: %s' % (user['user'], exc))
            else:
                print(user['user'])


def lambda_handler(event, context):
    concurrent_handler(batch_execution, global_config)

    return {
        'statusCode': 200,
        'body': json.dumps({'msg': 'DONE!'})
    }
