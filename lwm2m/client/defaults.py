import enum
import os

from aiocoap.numbers.constants import COAP_PORT


class Defaults(enum.Enum):
    SERVER_HOST = '::1'
    SERVER_PORT = COAP_PORT
    CLIENT_HOST = '::1'
    CLIENT_PORT = 56830
    LOGLEVEL = 'WARN'
    MODEL_LOADER = 'lwm2m.client.model:YamlModelLoader'
    MODEL_PATH = os.path.join(os.path.dirname(__file__), 'data')
