# ASGI Signing Middleware

The goal of this project is to provide a simple and straightforward way to securely sign data by providing ready-to-use middlewares, using [blake2signer](https://blake2signer.hackan.net/) as signing backend.

!!! question "Looking for another documentation version?"
    Check out [stable](https://blake2signer.hackan.net/en/stable/) (current tagged version), [latest](https://blake2signer.hackan.net/en/latest/) (current development version) or [each tagged version](https://readthedocs.org/projects/blake2signer).

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
    - or [FastAPI](https://fastapi.tiangolo.com/)
    - or [Starlite](https://starlite-api.github.io/starlite/)

Versions currently tested (check the [pipelines](https://gitlab.com/hackancuba/asgi_signing_middleware/-/pipelines)):

* CPython 3.8
* CPython 3.9
* CPython 3.10
* CPython 3.11
* [PyPy](https://www.pypy.org) 3.8
* [Stackless](https://github.com/stackless-dev/stackless/wiki) 3.8

## Documentation

These docs are generously hosted by [ReadTheDocs](https://readthedocs.org). Check the [project page](https://readthedocs.org/projects/asgi-signing-middleware) to know more and see different versions of these docs.

There are two major documentation versions, besides [each tagged version](https://readthedocs.org/projects/asgi-signing-middleware): [stable](https://asgi-signing-middleware.hackan.net/en/stable/) (current tagged version), and [latest](https://asgi-signing-middleware.hackan.net/en/latest/) (current development version).

## Notice

I'm not a cryptoexpert, so *this project needs a security review*. If you are one and can do it, please [contact me](https://hackan.net).

## License

**ASGI Signing Middleware** is made by [HacKan](https://hackan.net) under MPL v2.0. You are free to use, share, modify and share modifications under the terms of that [license](LICENSE).  Derived works may link back to the canonical repository: `https://gitlab.com/hackancuba/asgi-signing-middleware`.

    Copyright (C) 2022 HacKan (https://hackan.net)
    This Source Code Form is subject to the terms of the Mozilla Public
    License, v. 2.0. If a copy of the MPL was not distributed with this
    file, You can obtain one at https://mozilla.org/MPL/2.0/.
