"""Tests for the signed cookie module for FastAPI."""

import typing
from abc import abstractmethod
from unittest import mock

import pytest
from fastapi import FastAPI
from starlette.requests import Request
from starlette.testclient import TestClient

from ..cookie import CookieProperties
from ..cookie import JSONTypes
from ..cookie import SerializedSignedCookieMiddleware
from ..cookie import SimpleSignedCookieMiddleware
from ..cookie import TData
from ..types import TMiddleware


class SignedCookieMiddlewareTestsForFastAPIBase(typing.Generic[TMiddleware, TData]):
    """Base tests for a SignedCookieMiddleware for FastAPI."""

    secret = b'secretsecretsecret'
    state_attribute_name = 'cookie'
    cookie_name = 'my_cookie'
    cookie_ttl = 60

    @property
    def middleware_class(self) -> typing.Type[TMiddleware]:
        """Get this middleware class."""
        return typing.get_args(
            type(self).__orig_bases__[0],  # type: ignore
        )[0]

    @abstractmethod
    def modify_cookie_value(self, data: typing.Optional[TData]) -> TData:
        """Modify the cookie data as wanted. This is used by the `cookie_endpoint`."""

    def create_app(
        self,
        *,
        secret: typing.Optional[typing.Union[str, bytes]] = None,
        state_attribute_name: typing.Optional[str] = None,
        cookie_name: typing.Optional[str] = None,
        cookie_ttl: typing.Optional[int] = None,
        cookie_properties: typing.Optional[CookieProperties] = None,
        signer_kwargs: typing.Optional[typing.Dict[str, typing.Any]] = None,
    ) -> FastAPI:
        """Create a FastAPI application for the tests."""
        if state_attribute_name is None:
            state_attr = self.state_attribute_name
        else:
            state_attr = state_attribute_name

        app = FastAPI()
        app.add_middleware(
            self.middleware_class,
            secret=self.secret if secret is None else secret,
            state_attribute_name=state_attr,
            cookie_name=self.cookie_name if cookie_name is None else cookie_name,
            cookie_ttl=self.cookie_ttl if cookie_ttl is None else cookie_ttl,
            cookie_properties=cookie_properties,
            signer_kwargs=signer_kwargs,
        )

        @app.get('/')
        def root() -> typing.Dict[str, str]:
            """Main app endpoint."""
            return {
                'hello': 'world',
            }

        @app.get('/cookie')
        def cookie_endpoint(request: 'Request') -> None:
            """Endpoint that writes a cookie."""
            cookie_data = getattr(request.state, state_attr)
            modified_data = self.modify_cookie_value(cookie_data)
            setattr(request.state, state_attr, modified_data)

        return app

    def create_test_client(
        self,
        *,
        secret: typing.Optional[typing.Union[str, bytes]] = None,
        state_attribute_name: typing.Optional[str] = None,
        cookie_name: typing.Optional[str] = None,
        cookie_ttl: typing.Optional[int] = None,
        cookie_properties: typing.Optional[CookieProperties] = None,
        signer_kwargs: typing.Optional[typing.Dict[str, typing.Any]] = None,
    ) -> TestClient:
        """Create a test client directly."""
        app = self.create_app(
            secret=secret,
            state_attribute_name=state_attribute_name,
            cookie_name=cookie_name,
            cookie_ttl=cookie_ttl,
            cookie_properties=cookie_properties,
            signer_kwargs=signer_kwargs,
        )

        return TestClient(app)

    def create_app_and_test_client(
        self,
        *,
        secret: typing.Optional[typing.Union[str, bytes]] = None,
        state_attribute_name: typing.Optional[str] = None,
        cookie_name: typing.Optional[str] = None,
        cookie_ttl: typing.Optional[int] = None,
        cookie_properties: typing.Optional[CookieProperties] = None,
        signer_kwargs: typing.Optional[typing.Dict[str, typing.Any]] = None,
    ) -> typing.Tuple[FastAPI, TestClient]:
        """Create a FastAPI application and test client for the tests."""
        app = self.create_app(
            secret=secret,
            state_attribute_name=state_attribute_name,
            cookie_name=cookie_name,
            cookie_ttl=cookie_ttl,
            cookie_properties=cookie_properties,
            signer_kwargs=signer_kwargs,
        )

        return app, TestClient(app)

    def test_state_is_used(self) -> None:
        """Test that `request.state` is used."""
        app, client = self.create_app_and_test_client(state_attribute_name='msgs')

        @app.get('/state')
        def state_endpoint(request: 'Request') -> None:
            """Endpoint that asserts the state value."""
            assert 'existing' == request.state.msgs

        with mock.patch.object(
                self.middleware_class,
                'read_cookie',
                return_value='existing',
        ) as mock_read_cookie:
            response = client.get('/state')

        assert 200 == response.status_code
        assert response.json() is None
        mock_read_cookie.assert_called_once()

    def test_middleware_does_nothing_for_endpoints_that_wont_use_it(self) -> None:
        """Test that the middleware does not interfere with endpoints that won't use it."""
        client = self.create_test_client()

        with mock.patch.object(
                self.middleware_class,
                'write_cookie',
        ) as mock_write_cookie:
            response = client.get('/')

        assert 200 == response.status_code
        assert {
            'hello': 'world',
        } == response.json()
        mock_write_cookie.assert_not_called()

    @abstractmethod
    def test_cookie_is_set_and_signed(self) -> None:
        """Test that the cookie is properly set and signed."""

    @abstractmethod
    def test_signer_kwargs(self) -> None:
        """Test kwargs are passed to the signer."""

    def test_signer_kwargs_invalid(self) -> None:
        """Test invalid signer kwargs raises exception."""
        client = self.create_test_client(
            signer_kwargs={
                'deterministic': True,
                'secret': 'secret',
            },
        )

        with pytest.raises(
                ValueError,
                match='The `secret` should not be included in the signer kwargs',
        ):
            client.get('/')

        with pytest.raises(
                ValueError,
                match='The `secret` should not be included in the signer kwargs',
        ):
            client.get('/cookie')

    def test_existing_cookie_is_read_wrong_signature(self) -> None:
        """Test that existing cookie is read with wrong signature."""
        client = self.create_test_client()

        with mock.patch.object(
                self.middleware_class,
                'should_write_cookie',
        ) as mock_should_write_cookie:
            response = client.get(
                '/cookie',
                cookies={
                    self.cookie_name: 'jUSF_Zqz8NWPjT-c3cMcMQ.AAAnEA.existing',  # Wrong sig
                },
            )

        assert 200 == response.status_code
        assert response.json() is None
        mock_should_write_cookie.assert_called_once_with(
            unsigned_data=None,  # data in cookie is ignored
            state_data=self.modify_cookie_value(None),
        )

    def test_cookie_is_set_with_properties(self) -> None:
        """Test that the cookie is set with given properties."""
        client = self.create_test_client(
            cookie_properties={
                'path': '/cookie',
                'domain': 'hackan.net',
            },
        )

        with mock.patch('fastapi.Response.set_cookie') as mock_set_cookie:
            with mock.patch.object(
                    self.middleware_class,
                    'sign',
                    return_value='signed_data',
            ):
                response = client.get('/cookie')

        assert 200 == response.status_code
        assert response.json() is None

        mock_set_cookie.assert_called_once_with(
            key=self.cookie_name,
            value='signed_data',
            max_age=self.cookie_ttl,
            path='/cookie',
            domain='hackan.net',
            secure=False,
            httponly=False,
            samesite='lax',
        )


class TestSimpleSignedCookieMiddlewareForFastAPI(
        SignedCookieMiddlewareTestsForFastAPIBase[SimpleSignedCookieMiddleware, str],
):
    """Test SimpleSignedCookieMiddleware for FastAPI."""

    def modify_cookie_value(self, data: typing.Optional[str]) -> str:
        """Modify the cookie data as wanted. This is used by the `cookie_endpoint`."""
        return (data or '') + 'changed'

    def test_cookie_is_set_and_signed(self) -> None:
        """Test that the cookie is properly set and signed."""
        client = self.create_test_client()

        cookie_value = self.modify_cookie_value(None)
        response = client.get('/cookie')

        assert 200 == response.status_code
        assert response.json() is None
        assert [self.cookie_name] == response.cookies.keys()

        signed_cookie_value: str = response.cookies.get(self.cookie_name)
        assert cookie_value in signed_cookie_value  # It's signed
        assert len(cookie_value) < len(signed_cookie_value)
        assert 2 == signed_cookie_value.count('.')

    def test_signer_kwargs(self) -> None:
        """Test kwargs are passed to the signer."""
        client = self.create_test_client(
            signer_kwargs={
                'digest_size': 32,
                'deterministic': True,
                'personalisation': 'person',
            },
        )

        with mock.patch('blake2signer.bases.time', return_value=10000):
            with mock.patch('fastapi.Response.set_cookie') as mock_set_cookie:
                response = client.get('/cookie')

        assert 200 == response.status_code
        assert response.json() is None

        mock_set_cookie.assert_called_once_with(
            key=self.cookie_name,
            value='4dr7vcAheoRHyIDvveX4iFRtkiEBdkoy5W0GvefVbL0.AAAnEA.changed',
            max_age=self.cookie_ttl,
            path='/',
            domain=None,
            secure=False,
            httponly=False,
            samesite='lax',
        )

    def test_existing_signed_cookie_is_read(self) -> None:
        """Test that existing signed cookie is read."""
        client = self.create_test_client(signer_kwargs={'deterministic': True})

        with mock.patch('fastapi.Response.set_cookie') as mock_set_cookie:
            with mock.patch('blake2signer.bases.time', return_value=10000):
                response = client.get(
                    '/cookie',
                    cookies={
                        self.cookie_name: 'jUSF_Zqz8NWPjT-c3cMvMQ.AAAnEA.existing',
                    },
                )

        assert 200 == response.status_code
        assert response.json() is None
        mock_set_cookie.assert_called_once_with(
            key=self.cookie_name,
            value='2eOBgs64SlxJ6_8G0OKjyg.AAAnEA.existingchanged',
            max_age=self.cookie_ttl,
            path='/',
            domain=None,
            secure=False,
            httponly=False,
            samesite='lax',
        )


class TestSimpleSignedCookieMiddlewareForFastAPIPy38(TestSimpleSignedCookieMiddlewareForFastAPI):
    """Test SimpleSignedCookieMiddleware for FastAPI, hack for Pytest under Python 3.8."""

    __new__ = object.__new__


class TestSerializedSignedCookieMiddlewareForFastAPI(
        SignedCookieMiddlewareTestsForFastAPIBase[SerializedSignedCookieMiddleware, JSONTypes],
):
    """Test SerializedSignedCookieMiddleware for FastAPI."""

    def modify_cookie_value(self, data: typing.Optional[JSONTypes]) -> JSONTypes:
        """Modify the cookie data as wanted. This is used by the `cookie_endpoint`."""
        if data is None:
            return {
                'extra': 'data',
            }
        elif isinstance(data, dict):
            return {
                **data,
                **{
                    'extra': 'data',
                },
            }
        elif isinstance(data, list):
            return [*data, *['extra']]
        elif isinstance(data, (float, int)):
            return data + 1

        return data + 'changed'

    def test_cookie_is_set_and_signed(self) -> None:
        """Test that the cookie is properly set and signed."""
        client = self.create_test_client()

        cookie_value = 'eyJleHRyYSI6ImRhdGEifQ'
        response = client.get('/cookie')

        assert 200 == response.status_code
        assert response.json() is None
        assert [self.cookie_name] == response.cookies.keys()

        signed_cookie_value: str = response.cookies.get(self.cookie_name)
        assert cookie_value in signed_cookie_value  # It's signed
        assert len(cookie_value) < len(signed_cookie_value)
        assert 2 == signed_cookie_value.count('.')

    def test_signer_kwargs(self) -> None:
        """Test kwargs are passed to the signer."""
        client = self.create_test_client(
            signer_kwargs={
                'digest_size': 32,
                'deterministic': True,
                'personalisation': 'person',
            },
        )

        with mock.patch('blake2signer.bases.time', return_value=10000):
            with mock.patch('fastapi.Response.set_cookie') as mock_set_cookie:
                response = client.get('/cookie')

        assert 200 == response.status_code
        assert response.json() is None

        mock_set_cookie.assert_called_once_with(
            key=self.cookie_name,
            value='mNZnpY_lP9TKGJQs92mSKRo2aoBiQ9LhXXbH9rIXCjI.AAAnEA.eyJleHRyYSI6ImRhdGEifQ',
            max_age=self.cookie_ttl,
            path='/',
            domain=None,
            secure=False,
            httponly=False,
            samesite='lax',
        )

    @pytest.mark.parametrize(
        ('existing_value', 'expected_value'),
        (
            (  # string
                'd2_DaN4Tn-vWqAMFuHVOBw.AAAnEA.ImV4aXN0aW5nIg',
                'DObTeREEG5CqeWZMqR_BuA.AAAnEA.ImV4aXN0aW5nY2hhbmdlZCI',
            ),
            (  # int
                'EVRw10lZUe9j8619rp7IpQ.AAAnEA.MTAw',
                'QhyPzQA9eYuJtChhMAujRA.AAAnEA.MTAx',
            ),
            (  # dict
                'SeGdxygSYwwz0gaDQHv5Fw.AAAnEA.eyJzb21lIjoiZGF0YSJ9',
                'oE3A82_C0IU4CIc_LNI02Q.AAAnEA.eyJzb21lIjoiZGF0YSIsImV4dHJhIjoiZGF0YSJ9',
            ),
            (  # list
                'X63_2z5fRVUc9avmWTBQXA.AAAnEA.WyJzb21lIiwiZGF0YSJd',
                'fgtAa0aJgpAUfVqzka65MA.AAAnEA.WyJzb21lIiwiZGF0YSIsImV4dHJhIl0',
            ),
        ),
    )
    def test_existing_signed_cookie_is_read(
        self,
        existing_value: str,
        expected_value: str,
    ) -> None:
        """Test that existing signed cookie is read."""
        client = self.create_test_client(signer_kwargs={'deterministic': True})

        with mock.patch('fastapi.Response.set_cookie') as mock_set_cookie:
            with mock.patch('blake2signer.bases.time', return_value=10000):
                response = client.get(
                    '/cookie',
                    cookies={
                        self.cookie_name: existing_value,
                    },
                )

        assert 200 == response.status_code
        assert response.json() is None
        mock_set_cookie.assert_called_once_with(
            key=self.cookie_name,
            value=expected_value,
            max_age=self.cookie_ttl,
            path='/',
            domain=None,
            secure=False,
            httponly=False,
            samesite='lax',
        )


class TestSerializedSignedCookieMiddlewareForFastAPIPy38(
        TestSerializedSignedCookieMiddlewareForFastAPI,
):
    """Test SerializedSignedCookieMiddleware for FastAPI, hack for Pytest under Python 3.8."""

    __new__ = object.__new__
