import pytest

from lwm2m.client.logger import text_to_level


def test_valid_loglevels():
    valid_loglevels = ('DEBUG', 'INFO', 'WARN', 'WARNING',
                       'ERROR', 'FATAL', 'CRITICAL')
    for i in valid_loglevels:
        assert text_to_level(i) is not None


def test_invalid_loglevel_raises():
    with pytest.raises(ValueError):
        text_to_level('NONEXISTING')
