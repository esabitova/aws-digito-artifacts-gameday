import logging
import ssl

import requests
from OpenSSL import SSL
from boto3 import Session
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager
from requests.packages.urllib3.util import ssl_

CIPHERS = (
    'AES128-GCM-SHA256:ECDHE-RSA-AES128-SHA256:AES256-SHA'
)

log = logging.getLogger()


class TlsAdapter(HTTPAdapter):

    def __init__(self, ssl_options=0, **kwargs):
        self.ssl_options = ssl_options
        super(TlsAdapter, self).__init__(**kwargs)

    def init_poolmanager(self, *pool_args, **pool_kwargs):
        ctx = ssl_.create_urllib3_context(ciphers=CIPHERS, cert_reqs=ssl.CERT_REQUIRED, options=self.ssl_options)
        self.poolmanager = PoolManager(*pool_args,
                                       ssl_context=ctx,
                                       **pool_kwargs)


def send_incorrect_requests(boto3_session: Session, url: str, count: int):
    """
    Send incorrect requests against given URL endpoint
    :param boto3_session:
    :param url:
    :param count:
    """
    sess = requests.session()
    adp = TlsAdapter(SSL.OP_NO_TLSv1 | SSL.OP_NO_TLSv1_1 | SSL.OP_NO_TLSv1_2)
    sess.mount("https://", adp)
    logging.info(f'ELB start sending incorrect tls requests {count} times URL: "{url}"')
    for i in range(count):
        try:
            sess.get(url)
        except Exception:
            pass
    logging.info('ELB finished incorrect requests')
