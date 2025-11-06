import re

from projects._version import __version__


def test_version():
    version_re = r'^[0-9]{1,}.[0-9]{1,}.[0-9]{1,}$'
    assert re.match(version_re, __version__)
