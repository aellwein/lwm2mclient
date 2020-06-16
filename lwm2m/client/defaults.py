import enum
from aiocoap.numbers.constants import COAP_PORT


class Defaults(enum.Enum):
    SERVER_HOST = '::1'
    SERVER_PORT = COAP_PORT
    CLIENT_HOST = '::1'
    CLIENT_PORT = 56830
    LOGLEVEL = 'WARN'
