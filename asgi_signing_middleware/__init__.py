"""ASGI signing middlewares.

Middlewares for ASGI applications such as FastAPI or Starlette, that allows to easily
sign data using `blake2signer <https://blake2signer.hackan.net/>`_.

To use in any FastAPI/Starlette app, do as with any other middleware:

```python
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

ASGI Signing Middleware is made by `HacKan <https://hackan.net>`_ under MPL v2.0. You are
free to use, share, modify and share modifications under the terms of that license.
Derived works may link back to the canonical repository:
https://gitlab.com/hackancuba/asgi-signing-middleware.

---

Copyright (C) 2022 HacKan (https://hackan.net)
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

from .cookie import SerializedSignedCookieMiddleware
from .cookie import SimpleSignedCookieMiddleware

__version__ = '0.1.2'

__all__ = (
    'SerializedSignedCookieMiddleware',
    'SimpleSignedCookieMiddleware',
)
