# Examples

The following examples are working code and should run as-is.

## Tl; Dr

If you don't have time to read (_ain't nobody got time fo' that!_), check out this short intro example, it is pretty much self explanatory.

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
    print(cookie_data)

    # ...

    # This will be signed and written into the cookie
    request.state.messages = {'A Title': 'The message', 'Another title': 'With another msg'}
```

## Example app

This very simple app has an endpoint in the root path (`/`) that displays a value from a signed cookie, which can be set through the query parameter `value` (as in `http://127.0.0.1:8000/?value=some%20value`).

It will append every new value to the previous one, show it in the JSON response as `{"value":"<value>"}`, and store it signed in a cookie named `cookie`.

!!! tip
    Copy this example into a file named `app.py` and run it with `uvicorn --reload app:app`.

!!! success
    If you try to manually change the cookie value, it will reset it to an empty string. That's because the cookie is signed, and therefore has tamper protection.

=== "Starlette"

    ```python
    """Example Starlette app."""

    from starlette.applications import Starlette
    from starlette.middleware import Middleware
    from starlette.requests import Request
    from starlette.responses import JSONResponse
    from starlette.routing import Route

    from asgi_signing_middleware import SimpleSignedCookieMiddleware


    async def root(request: Request) -> JSONResponse:
        """Root endpoint.

        Input some string value through the `value` query parameter. That value will
        be appended to the previous one, signed and stored in a cookie named `cookie`.
        This will be displayed in the response as a JSON message of the form
        `{"value": "<value>"}`.

        The signature will be valid for 1', after that the value will reset to an
        empty string.

        Args:
            request: The request.

        Returns:
            A JSON response with the final value.
        """
        value: str = request.query_params.get('value', '')
        prev_value: str = request.state.msgs or ''
        request.state.msgs = prev_value + value

        return JSONResponse({'value': request.state.msgs})


    # Run with `uvicorn --reload <file name without extension>:app`
    app = Starlette(
        debug=True,
        routes=[
            Route('/', root),
        ],
        middleware=[
            Middleware(
                SimpleSignedCookieMiddleware,
                secret='secret' * 3,
                state_attribute_name='msgs',
                cookie_name='cookie',
                cookie_ttl=60,
            ),
        ],
    )
    ```

=== "FastAPI"

    ```python
    """Example FastAPI app."""

    from fastapi import FastAPI
    from fastapi import Request

    from asgi_signing_middleware import SimpleSignedCookieMiddleware

    # Run with `uvicorn --reload <file name without extension>:app`
    app = FastAPI(debug=True)
    app.add_middleware(
        SimpleSignedCookieMiddleware,
        secret='secret' * 3,
        state_attribute_name='msgs',
        cookie_name='cookie',
        cookie_ttl=60,
    )

    
    @app.get('/')
    async def root(request: Request) -> dict[str, str]:
        """Root endpoint.

        Input some string value through the `value` query parameter. That value will
        be appended to the previous one, signed and stored in a cookie named `cookie`.
        This will be displayed in the response as a JSON message of the form
        `{"value": "<value>"}`.

        The signature will be valid for 1', after that the value will reset to an
        empty string.

        Args:
            request: The request.

        Returns:
            A JSON response with the final value.
        """
        value: str = request.query_params.get('value', '')
        prev_value: str = request.state.msgs or ''
        request.state.msgs = prev_value + value

        return {
            'value': request.state.msgs,
        }
    ```
