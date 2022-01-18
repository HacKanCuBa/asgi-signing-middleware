"""Signed cookie FastAPI/Starlette middleware.

These base classes allows you to create a generic middleware that uses a signed cookie to
securely store data. Additionally, it provides two ready-to-use middlewares to handle simple
and complex data structures.
"""

import typing
from abc import abstractmethod

from blake2signer import Blake2SerializerSigner
from blake2signer import Blake2TimestampSigner
from blake2signer.errors import SignedDataError
from starlette.middleware.base import BaseHTTPMiddleware

from .types import CookieProperties
from .types import JSONTypes
from .types import TData
from .types import TSigner

if typing.TYPE_CHECKING:
    from starlette.requests import Request
    from starlette.responses import Response
    from starlette.middleware.base import RequestResponseEndpoint
    from starlette.types import ASGIApp


class SignedCookieMiddlewareBase(
        typing.Generic[TSigner, TData],
        BaseHTTPMiddleware,
):
    """Base to create a middleware that can store signed data into a cookie.

    It uses the `request.state` (see https://www.starlette.io/requests/#other-state) to
    communicate with request handlers (views), so simply define a name used with the state,
    as in `request.state.my_cookie`, where data read from the cookie is stored there, and
    data produced by the request handler (stored in the state) is written to the cookie.
    """

    def __init__(
        self,
        app: 'ASGIApp',
        *,
        secret: typing.Union[str, bytes],
        state_attribute_name: str,
        cookie_name: str,
        cookie_ttl: int,
        cookie_properties: typing.Optional[CookieProperties] = None,
        signer_kwargs: typing.Optional[typing.Dict[str, typing.Any]] = None,
    ) -> None:  # noqa: D417  # it's a false positive
        """Create a signed cookie middleware.

        Args:
            app: An ASGI application instance.

        Keyword Args:
            secret: The signing secret.
            state_attribute_name: The attribute name used for `request.state`.
            cookie_name: The name of the cookie.
            cookie_ttl: The cookie time-to-live in seconds.
            cookie_properties (optional): Additional cookie properties:
                path: Cookie path (defaults to '/').
                domain: Cookie domain.
                secure: True to use HTTPS, False otherwise (default).
                httpsonly: True to prevent the cookie from being used by JS, False
                    otherwise (default).
                samesite: Define cookie restriction: lax, strict or none.
            signer_kwargs (optional): Additional keyword arguments for the signer.
        """
        super().__init__(app)

        self.secret: typing.Union[str, bytes] = secret
        self.state_attribute_name: str = state_attribute_name
        self.signer_kwargs: typing.Dict[str, typing.Any] = signer_kwargs or {}
        self.cookie_name: str = cookie_name
        self.cookie_ttl: int = cookie_ttl

        self._cookie_properties: CookieProperties = cookie_properties or {}

        self.signer_class: typing.Type[TSigner] = self.get_signer_class()

    def get_signer_class(self) -> typing.Type[TSigner]:
        """Get the signer class."""
        # This is kinda a hack to get the signer class from the `Generic` args, and only
        # works on Python 3.8+ (see https://stackoverflow.com/a/50101934 and PEP 560).
        # You can alternatively override this method and define the signer class directly,
        # I.E.: return Blake2TimestampSigner
        return typing.get_args(type(self).__orig_bases__[0])[0]  # type: ignore

    def get_signer(self) -> TSigner:
        """Get an instance of the signer to use with `sign` and `unsign` methods."""
        personalisation = type(self).__name__ + self.cookie_name

        signer_kwargs = self.signer_kwargs.copy()

        if 'secret' in signer_kwargs:
            raise ValueError('The `secret` should not be included in the signer kwargs')

        if 'personalisation' in signer_kwargs:
            personalisation += signer_kwargs.pop('personalisation')

        return self.signer_class(
            self.secret,
            personalisation=personalisation,
            **signer_kwargs,
        )

    @abstractmethod
    def sign(self, data: TData) -> str:
        """Sign data with the signer."""

    @abstractmethod
    def unsign(self, data: str) -> TData:
        """Unsign data with the signer."""

    @property
    def cookie_properties(self) -> CookieProperties:
        """Get the cookie properties as a dict.

        Override this method if you want to set different defaults.

        Returns:
            Cookie properties as a dict.
        """
        properties = {
            'path': '/',
            'domain': None,
            'secure': False,
            'httponly': False,
            'samesite': 'lax',
        }
        properties.update(self._cookie_properties)

        return properties

    # noinspection PyMethodMayBeStatic
    def should_write_cookie(
        self,
        *,
        unsigned_data: typing.Optional[TData],
        state_data: TData,
    ) -> bool:
        """Return True if data should be written to the cookie, False otherwise.

        This method exists to avoid writing cookies on every request needlessly. Overwrite
        this method with a proper data comparison, or just return True to always write the
        cookie.

        Returns:
            True if new data should be written to the cookie, False otherwise.
        """
        return state_data != unsigned_data

    def read_cookie(self, request: 'Request') -> TData:
        """Get data from the cookie, checking its signature.

        Note that if the signature is wrong, an exception is raised (any subclass of
        SignedDataError).

        Returns:
            Data from the cookie.

        Raises:
            SignedDataError: the signature was wrong, missing, or otherwise incorrect.
        """
        signed_data = request.cookies.get(self.cookie_name, '')
        data: TData = self.unsign(signed_data)  # may raise SignedDataError

        return data

    def write_cookie(self, data: TData, response: 'Response') -> None:
        """Write the cookie in the response after signing it."""
        signed_data = self.sign(data)

        response.set_cookie(
            key=self.cookie_name,
            value=signed_data,
            max_age=self.cookie_ttl,
            **self.cookie_properties,  # type: ignore
        )

    async def dispatch(
        self,
        request: 'Request',
        call_next: 'RequestResponseEndpoint',
    ) -> 'Response':
        """Read data from, and write data to, a signed cookie.

        This middleware with inject the data in the request state, and will write to the
        cookie after the request handler has acted.

        Returns:
            A response.
        """
        data: typing.Optional[TData]
        try:
            data = self.read_cookie(request)
        except SignedDataError:  # some tampering, maybe we changed the secret...
            data = None

        setattr(request.state, self.state_attribute_name, data)

        response = await call_next(request)

        new_data: typing.Optional[TData] = getattr(
            request.state,
            self.state_attribute_name,
            None,
        )

        if new_data is not None and self.should_write_cookie(
                unsigned_data=data,
                state_data=new_data,
        ):
            self.write_cookie(new_data, response)

        return response


class SimpleSignedCookieMiddleware(
        SignedCookieMiddlewareBase[Blake2TimestampSigner, str],
):
    """Middleware that can sign string data and store it into a cookie.

    Use this middleware if you want to store simple data as a string into a cookie.

    It uses the `request.state` (see https://www.starlette.io/requests/#other-state) to
    communicate with request handlers (views), so simply define a name used with the state,
    as in `request.state.my_cookie`, where data read from the cookie is stored there, and
    data produced by the request handler (stored in the state) is written to the cookie.
    """

    def sign(self, data: str) -> str:
        """Sign data with the signer."""
        return self.get_signer().sign(data).decode()

    def unsign(self, data: str) -> str:
        """Unsign data with the signer."""
        return self.get_signer().unsign(data, max_age=self.cookie_ttl).decode()


class SerializedSignedCookieMiddleware(
        SignedCookieMiddlewareBase[Blake2SerializerSigner, JSONTypes],
):
    """Middleware that can serialize data and sign it into a cookie.

    Use this middleware if you want to store certain complex data structures into a cookie.
    Note that this middleware is slower than the SimpleSignedCookieMiddleware, but ideal
    for any kind of data structure.

    It uses the `request.state` (see https://www.starlette.io/requests/#other-state) to
    communicate with request handlers (views), so simply define a name used with the state,
    as in `request.state.my_cookie`, where data read from the cookie is stored there, and
    data produced by the request handler (stored in the state) is written to the cookie.

    Inherit from this class to create a concrete middleware and implement the following
    properties:

    secret: define the signing secret (it should probably come from a global configuration).
    cookie_name: define the name of the cookie.
    cookie_ttl: define the time-to-live for the cookie, in seconds.
    state_attribute_name: define the name used for the state attribute.
    """

    def get_signer(self) -> Blake2SerializerSigner:
        """Get an instance of the signer to use with `sign` and `unsign` methods."""
        self.signer_kwargs.setdefault('max_age', self.cookie_ttl)

        return super().get_signer()

    def sign(self, data: JSONTypes) -> str:
        """Sign data with the signer."""
        return self.get_signer().dumps(data)

    def unsign(self, data: str) -> JSONTypes:
        """Unsign data with the signer."""
        return self.get_signer().loads(data)
