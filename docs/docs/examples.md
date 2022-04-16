# Examples

The following examples are working code and should run as-is.

## Tl; Dr

If you don't have time to read (_ain't nobody got time fo' that!_), check out this short intro example, it is pretty much self-explanatory.

The state attribute will be populated with a [`CookieData`](cookie.md#asgi_signing_middleware.cookie.CookieData) object, containing the actual data, and any exception got from unsigning it. When unsigning fails, the data will be null.

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
    cookie_data: typing.Optional[typing.Dict[str, str]] = request.state.messages.data
    print(cookie_data)  # CookieData(data=..., exc=...)

    # ...

    # This will be signed and written into the cookie
    request.state.messages.data = {'A Title': 'The message', 'Another title': 'With another msg'}
```

## Simple signed cookie app

This very simple app has an endpoint in the root path (`/`) that displays a value from a signed cookie, which can be set through the query parameter `value` (as in `http://127.0.0.1:8000/?value=some%20value`). It shows how to implement the [SimpleSignedCookieMiddleware](cookie.md#asgi_signing_middleware.cookie.SimpleSignedCookieMiddleware).

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
        prev_value: str = request.state.msgs.data or ''
        new_value = prev_value + value
        request.state.msgs.data = new_value

        return JSONResponse({'value': new_value})


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
    async def root(request: Request, value: str = '') -> dict[str, str]:
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
        prev_value: str = request.state.msgs.data or ''
        new_value = prev_value + value
        request.state.msgs.data = new_value

        return {
            'value': new_value,
        }
    ```

=== "Starlite"

    ```python
    """Example Starlite app."""

    from starlette.middleware import Middleware
    from starlite import Request
    from starlite import Starlite
    from starlite import get

    from asgi_signing_middleware import SimpleSignedCookieMiddleware


    @get('/')
    async def root(request: Request, value: str = '') -> dict[str, str]:
        """Root endpoint.

        Input some string value through the `value` query parameter. That value will
        be appended to the previous one, signed and stored in a cookie named `cookie`.
        This will be displayed in the response as a JSON message of the form
        `{"value": "<value>"}`.

        The signature will be valid for 1', after that the value will reset to an
        empty string.

        Args:
            request: The request.
            value: The string value.

        Returns:
            A JSON response with the final value.
        """
        prev_value: str = request.state.msgs.data or ''
        new_value = prev_value + value
        request.state.msgs.data = new_value

        return {
            'value': new_value,
        }


    # Run with `uvicorn --reload <file name without extension>:app`
    app = Starlite(
        debug=True,
        route_handlers=[
            root,
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

## Cookie-based authentication app

This very simple app has an endpoint in the root path (`/`) that salutes a logged-in user, and rejects any other. You can log in by sending the payload `{"username": "<username>"}` to `POST /login`. It shows how to implement the [SerializedSignedCookieMiddleware](cookie.md#asgi_signing_middleware.cookie.SerializedSignedCookieMiddleware).

!!! tip
    Copy this example into a file named `app.py` and run it with `uvicorn --reload app:app`.

??? abstract "Usage with `curl`"
    1. Visit the root, get rejected: `curl -v 127.0.0.1:8000/`
    ```
    *   Trying 127.0.0.1:8000...
    * Connected to 127.0.0.1 (127.0.0.1) port 8000 (#0)
    > GET / HTTP/1.1
    > Host: 127.0.0.1:8000
    > User-Agent: curl
    > Accept: */*
    >
    * Mark bundle as not supporting multiuse
    < HTTP/1.1 403 Forbidden
    < date: Sun, 10 Apr 2022 00:06:30 GMT
    < server: uvicorn
    < content-length: 9
    < content-type: text/plain; charset=utf-8
    <
    * Connection #0 to host 127.0.0.1 left intact
    ```

    2. Register your user: `curl -v -H 'content-type:application/json' -d '{"username": "hackan"}' 127.0.0.1:8000/login`
    ```
    *   Trying 127.0.0.1:8000...
    * Connected to 127.0.0.1 (127.0.0.1) port 8000 (#0)
    > POST /login HTTP/1.1
    > Host: 127.0.0.1:8000
    > User-Agent: curl
    > Accept: */*
    > Content-Length: 22
    > Content-Type: application/json
    >
    * upload completely sent off: 22 out of 22 bytes
    * Mark bundle as not supporting multiuse
    < HTTP/1.1 200 OK
    < date: Sun, 10 Apr 2022 00:07:15 GMT
    < server: uvicorn
    < content-length: 23
    < content-type: application/json
    < set-cookie: user=8qQsAov34-_hv0g4_4fcz1YM7qvpeRDUTQRN-Q.YlIftA.eyJ1c2VybmFtZSI6ImhhY2thbiIsInJlZ2lzdGVyZWQtb24iOjE2NDk1NDkyMzYuNjUxMzkyfQ; HttpOnly; Max-Age=30 days, 0:00:00; Path=/; SameSite=strict
    <
    * Connection #0 to host 127.0.0.1 left intact
    ```
    3. Store the cookie in a variable for easier handling: `cookie='user=8qQsAov34-_hv0g4_4fcz1YM7qvpeRDUTQRN-Q.YlIftA.eyJ1c2VybmFtZSI6ImhhY2thbiIsInJlZ2lzdGVyZWQtb24iOjE2NDk1NDkyMzYuNjUxMzkyfQ; HttpOnly; Max-Age=30 days, 0:00:00; Path=/; SameSite=strict'`

    4. Request the root page with the cookie: `curl -v -H "cookie:$cookie" 127.0.0.1:8000/`
    ```
    *   Trying 127.0.0.1:8000...
    * Connected to 127.0.0.1 (127.0.0.1) port 8000 (#0)
    > GET / HTTP/1.1
    > Host: 127.0.0.1:8000
    > User-Agent: curl
    > Accept: */*
    > cookie:user=4EXmoGS-Dxcv_N0MLMIPtDV2q59cxYF4KX1h9g.YlIdrA.eyJ1c2VybmFtZSI6ImhhY2thbiIsInJlZ2lzdGVyZWQtb24iOjE2NDk1NDg3MTYuMTM1Mjc2fQ; HttpOnly; Max-Age=30 days, 0:00:00; Path=/; SameSite=strict
    >
    * Mark bundle as not supporting multiuse
    < HTTP/1.1 200 OK
    < date: Sun, 10 Apr 2022 00:10:22 GMT
    < server: uvicorn
    < content-length: 54
    < content-type: application/json
    <
    * Connection #0 to host 127.0.0.1 left intact
    {"hello":"hackan","since":"2022-04-09T23:58:36+00:00"}
    ```

!!! success
    If you try to manually change the cookie value, you will receive a 401 error with the text "Invalid authentication cookie". That's because the cookie is signed, and therefore has tamper protection.

=== "Starlette"

    ```python
    """Very basic cookie-based authorization Starlette app."""

    import typing
    from datetime import datetime
    from datetime import timedelta
    from datetime import timezone

    from starlette.applications import Starlette
    from starlette.authentication import AuthCredentials
    from starlette.authentication import AuthenticationBackend
    from starlette.authentication import AuthenticationError
    from starlette.authentication import BaseUser
    from starlette.authentication import SimpleUser
    from starlette.authentication import requires
    from starlette.exceptions import HTTPException
    from starlette.middleware import Middleware
    from starlette.middleware.authentication import AuthenticationMiddleware
    from starlette.requests import HTTPConnection
    from starlette.requests import Request
    from starlette.responses import JSONResponse, Response
    from starlette.routing import Route
    from starlette.status import HTTP_401_UNAUTHORIZED

    from asgi_signing_middleware import SerializedSignedCookieMiddleware


    class SignedCookieAuthBackend(AuthenticationBackend):
        """An authentication backend that stores data in a signed cookie."""

        async def authenticate(
            self,
            conn: HTTPConnection,
        ) -> typing.Optional[typing.Tuple[AuthCredentials, BaseUser]]:
            """Authenticate the user."""
            cookie_data = conn.state.user
            if cookie_data.exc:
                raise AuthenticationError('Invalid authentication cookie')

            user_data = cookie_data.data
            if not user_data:
                return

            return AuthCredentials(['authenticated']), SimpleUser(user_data['username'])


    @requires('authenticated')
    async def root(request: Request) -> JSONResponse:
        """Root endpoint (access restricted)."""
        cookie_data = request.state.user
        user_data = cookie_data.data
        since = datetime.fromtimestamp(
            user_data['registered-on'],
            tz=timezone.utc,
        ).isoformat(timespec='seconds')

        return JSONResponse({
            'hello': user_data['username'],
            'since': since,
        })


    async def login(request: Request) -> JSONResponse:
        """Log in with given user."""
        unauthorized_exception = HTTPException(HTTP_401_UNAUTHORIZED, 'User data is not valid')

        try:
            json_body = await request.json()
        except ValueError:
            raise unauthorized_exception

        try:
            username = json_body['username']
        except KeyError:
            raise unauthorized_exception

        request.state.user.data = {
            'username': username,
            'registered-on': datetime.now(tz=timezone.utc).timestamp(),
        }

        return JSONResponse({'registered': username})


    @requires('authenticated')
    async def logout(request: Request) -> Response:
        """Log out, if you were logged in."""
        # You should probably implement some sort of blocklist for the actual cookie data
        request.state.user.data = {}
    
        return Response(status_code=204)


    # Run with `uvicorn --reload <file name without extension>:app`
    app = Starlette(
        debug=True,
        routes=[
            Route('/', root),
            Route('/login', login, methods=['POST']),
            Route('/logout', logout, methods=['POST']),
        ],
        # The order matters! Set the SerializedSignedCookieMiddleware first, so the request
        # state is properly set on the SignedCookieAuthBackend
        middleware=[
            Middleware(
                SerializedSignedCookieMiddleware,
                secret='secret' * 3,
                state_attribute_name='user',
                cookie_name='user',
                cookie_ttl=timedelta(days=30),
                cookie_properties={
                    'samesite': 'strict',
                    'httponly': True,
                },
            ),
            Middleware(AuthenticationMiddleware, backend=SignedCookieAuthBackend()),
        ],
    )
    ```

=== "FastAPI"

    ```python
    """Very basic cookie-based authorization FastAPI app."""

    import typing
    from datetime import datetime
    from datetime import timedelta
    from datetime import timezone

    from fastapi import Body
    from fastapi import FastAPI
    from fastapi.requests import HTTPConnection
    from fastapi.requests import Request
    from starlette.authentication import AuthCredentials
    from starlette.authentication import AuthenticationBackend
    from starlette.authentication import AuthenticationError
    from starlette.authentication import BaseUser
    from starlette.authentication import SimpleUser
    from starlette.authentication import requires
    from starlette.middleware.authentication import AuthenticationMiddleware

    from asgi_signing_middleware import SerializedSignedCookieMiddleware


    class SignedCookieAuthBackend(AuthenticationBackend):
        """An authentication backend that stores data in a signed cookie."""

        async def authenticate(
            self,
            conn: HTTPConnection,
        ) -> typing.Optional[typing.Tuple[AuthCredentials, BaseUser]]:
            """Authenticate the user."""
            cookie_data = conn.state.user
            if cookie_data.exc:
                raise AuthenticationError('Invalid authentication cookie')

            user_data = cookie_data.data
            if not user_data:
                return None

            return AuthCredentials(['authenticated']), SimpleUser(user_data['username'])


    # Run with `uvicorn --reload <file name without extension>:app`
    app = FastAPI(debug=True)

    # The order matters! Set the SerializedSignedCookieMiddleware second (because FastAPI prepends
    # middlewares), so the request state is properly set on the SignedCookieAuthBackend
    app.add_middleware(
        AuthenticationMiddleware,
        backend=SignedCookieAuthBackend(),
    )
    app.add_middleware(
        SerializedSignedCookieMiddleware,
        secret='secret' * 3,
        state_attribute_name='user',
        cookie_name='user',
        cookie_ttl=timedelta(days=30),
        cookie_properties={
            'samesite': 'strict',
            'httponly': True,
        },
    )


    @app.get('/')
    @requires('authenticated')
    async def root(request: Request):
        """Root endpoint (access restricted)."""
        cookie_data = request.state.user
        user_data = cookie_data.data
        since = datetime.fromtimestamp(
            user_data['registered-on'],
            tz=timezone.utc,
        ).isoformat(timespec='seconds')

        return {
            'hello': user_data['username'],
            'since': since,
        }


    @app.post('/login')
    async def login(request: Request, username: str = Body(..., embed=True)):
        """Log in with given user."""
        request.state.user.data = {
            'username': username,
            'registered-on': datetime.now(tz=timezone.utc).timestamp(),
        }

        return {
            'registered': username,
        }


    @app.post('/logout', status_code=204)
    @requires('authenticated')
    async def logout(request: Request) -> None:
        """Log out, if you were logged in."""
        # You should probably implement some sort of blocklist for the actual cookie data
        request.state.user.data = {}
    ```

=== "StarLite"

    ```python
    """Very basic cookie-based authorization StarLite app."""

    import typing
    from datetime import datetime
    from datetime import timedelta
    from datetime import timezone

    from starlette.middleware import Middleware
    from starlette.requests import HTTPConnection
    from starlite import AbstractAuthenticationMiddleware
    from starlite import AuthenticationResult
    from starlite import HTTPRouteHandler
    from starlite import NotAuthorizedException
    from starlite import Request
    from starlite import Starlite
    from starlite import get
    from starlite import post

    from asgi_signing_middleware import SerializedSignedCookieMiddleware


    def authenticated_guard(request: Request, _: HTTPRouteHandler) -> None:
        """Guard for authenticated users."""
        if not request.user:
            raise NotAuthorizedException('You need to login first')


    class SignedCookieAuthMiddleware(AbstractAuthenticationMiddleware):
        """An authentication middleware that stores data in a signed cookie."""

        async def authenticate_request(self, request: HTTPConnection) -> AuthenticationResult:
            """Authenticate the user."""
            # retrieve the auth header
            cookie_data = request.state.user
            if cookie_data.exc:
                raise NotAuthorizedException('Invalid authentication cookie')

            user_data = cookie_data.data
            if not user_data:
                return AuthenticationResult(user=None)

            return AuthenticationResult(user=user_data)


    @get('/', guards=[authenticated_guard])
    async def root(request: Request) -> typing.Dict[str, str]:
        """Root endpoint (access restricted)."""
        cookie_data = request.state.user
        user_data = cookie_data.data
        since = datetime.fromtimestamp(
            user_data['registered-on'],
            tz=timezone.utc,
        ).isoformat(timespec='seconds')

        return {
            'hello': user_data['username'],
            'since': since,
        }


    @post('/login')
    async def login(request: Request) -> typing.Dict[str, str]:
        """Log in with given user."""
        unauthorized_exception = NotAuthorizedException('User data is not valid')

        try:
            json_body = await request.json()
        except ValueError:
            raise unauthorized_exception

        try:
            username = json_body['username']
        except KeyError:
            raise unauthorized_exception

        request.state.user.data = {
            'username': username,
            'registered-on': datetime.now(tz=timezone.utc).timestamp(),
        }

        return {
            'registered': username,
        }


    @post('/logout', guards=[authenticated_guard], status_code=204)
    async def logout(request: Request) -> None:
        """Log out, if you were logged in."""
        # You should probably implement some sort of blocklist for the actual cookie data
        request.state.user.data = {}


    # Run with `uvicorn --reload <file name without extension>:app`
    app = Starlite(
        debug=True,
        route_handlers=[
            root,
            login,
        ],
        # The order matters! Set the SerializedSignedCookieMiddleware second (because StarLite
        # configures them the other way around), so the request state is properly set on the
        # SignedCookieAuthBackend
        middleware=[
            SignedCookieAuthMiddleware,
            Middleware(
                SerializedSignedCookieMiddleware,
                secret='secret' * 3,
                state_attribute_name='user',
                cookie_name='user',
                cookie_ttl=timedelta(days=30),
                cookie_properties={
                    'samesite': 'strict',
                    'httponly': True,
                },
            ),
        ],
    )
    ```
