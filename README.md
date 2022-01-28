[![Pipeline Status](https://img.shields.io/gitlab/pipeline/hackancuba/asgi-signing-middleware/develop?style=plastic)](https://gitlab.com/hackancuba/asgi-signing-middleware/-/pipelines?page=1&scope=all&ref=develop)
[![Coverage Report](https://img.shields.io/gitlab/coverage/hackancuba/asgi-signing-middleware/develop?style=plastic)](https://gitlab.com/hackancuba/asgi-signing-middleware/-/commits/develop)
[![PyPI Version](https://img.shields.io/pypi/v/asgi-signing-middleware?color=light%20green&style=plastic)](https://pypi.org/project/asgi-signing-middleware)
[![PyPI Python Versions](https://img.shields.io/pypi/pyversions/asgi-signing-middleware?color=light%20green&style=plastic)](https://pypi.org/project/asgi-signing-middleware)
[![License](https://img.shields.io/pypi/l/asgi-signing-middleware?color=light%20green&style=plastic)](https://gitlab.com/hackancuba/asgi-signing-middleware/-/blob/main/LICENSE)
[![Follow Me on Twitter](https://img.shields.io/twitter/follow/hackancuba?color=light%20green&style=plastic)](https://twitter.com/hackancuba)

# ASGI Signing Middleware

The goal of this project is to provide a simple and straightforward way to securely sign data by providing ready-to-use middlewares, using [blake2signer](https://blake2signer.hackan.net/) as signing backend.

## Why would I need to use it?

If you need to store some data (state, generally), and want to avoid using a trusted DB for performance reasons, it is usually advisable to sign said data. This package will help you achieve that with ease, ready-to-use middlewares, without you needing to think on the details: just provide a signing secret and let this package handle the rest.

## Why would I want to use it?

Because it is a relatively *small* (around 100 logical lines of code), *simple* (usage is very straight-forward) yet very *customizable* and *fast* middleware data signer. My idea is to keep it as uncomplicated as possible without much room to become a *footgun*. All *defaults are very sane* (secure) and everything *just works* out of the box.

## Goals

* Be safe and secure.
* Be simple and straightforward.
* Follow [semver](https://semver.org/).
* Be always typed.
* 100% coverage.

### Secondary goals

* If possible, maintain active Python versions (3.8+).

## Installing

This package is hosted on [PyPi](https://pypi.org/project/asgi_signing_middleware) so just:

* `python3 -m pip install asgi-signing-middleware`
* `poetry add asgi-signing-middleware`
* `pipenv install asgi-signing-middleware`

You can check the [releases' page](https://gitlab.com/hackancuba/asgi-signing-middleware/-/releases) for package hashes and signatures.

### Requirements

- Python 3.8+
- [blake2signer](https://blake2signer.hackan.net/)
- [starlette](https://starlette.io/)
  - or FastAPI
  - or Starlite

Versions currently tested (check the [pipelines](https://gitlab.com/hackancuba/asgi_signing_middleware/-/pipelines)):

* CPython 3.8
* CPython 3.9
* CPython 3.10
* CPython 3.11
* [PyPy](https://www.pypy.org) 3.8
* [Stackless](https://github.com/stackless-dev/stackless/wiki) 3.8

## Tl; Dr Example

```python
"""Tl;dr example."""

import typing

from fastapi import FastAPI
from fastapi import Request

from asgi_signing_middleware import SerializedSignedCookieMiddleware

app = FastAPI()
app.add_middleware(
    SerializedSignedCookieMiddleware,  # Any of the middlewares
    # Follows the middleware parameters
    secret=b'a very, very secret thing',  # This should probably come from some configs
    state_attribute_name='messages',  # Use in a request handler as `request.state.messages`
    cookie_name='my_cookie',
    cookie_ttl=60 * 5,  # 5 minutes, in seconds
    # You can also set extra signer kwargs and cookie properties, check the middleware
    # init for more info.
)

@app.get('/cookie')
def cookie_endpoint(request: Request) -> None:
    # This will only have data that was correctly signed, or None
    cookie_data: typing.Optional[typing.Dict[str, str]] = request.state.messages

    # ...

    # This will be signed and written into the cookie
    request.state.messages = {'A Title': 'The message', 'Another title': 'With another msg'}
```

> Tip: all modules, classes, methods and functions are documented so don't doubt asking for `help()`.

## Documentation

Check out this [project docs online](https://asgi-signing-middleware.hackan.net) or locally with `inv docs`. Alternatively, build them locally using `inv docs --build`.

## Notice

I'm not a cryptoexpert, so *this project needs a security review*. If you are one and can do it, please [contact me](https://hackan.net).

## License

**ASGI Signing Middleware** is made by [HacKan](https://hackan.net) under MPL v2.0. You are free to use, share, modify and share modifications under the terms of that [license](LICENSE).  Derived works may link back to the canonical repository: `https://gitlab.com/hackancuba/asgi-signing-middleware`.

    Copyright (C) 2022 HacKan (https://hackan.net)
    This Source Code Form is subject to the terms of the Mozilla Public
    License, v. 2.0. If a copy of the MPL was not distributed with this
    file, You can obtain one at https://mozilla.org/MPL/2.0/.

----
