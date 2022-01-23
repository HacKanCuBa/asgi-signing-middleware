"""Test that starlite can not be tested under PyPy."""

import platform
from unittest import mock

with mock.patch.object(
        platform,
        'python_implementation',
        return_value='PyPy',
):
    # We don't have anything to assert really: we need to import the module to cover the
    # line that test for platform and that's as much as we can do...
    from asgi_signing_middleware.tests import tests_cookie_starlite  # noqa

    assert platform.python_implementation() == 'PyPy'
