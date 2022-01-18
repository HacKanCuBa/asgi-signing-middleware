"""Types definition."""

import typing

from blake2signer import Blake2SerializerSigner
from blake2signer import Blake2TimestampSigner

# Generic signer type, bound to blake2signer's signers
TSigner = typing.TypeVar('TSigner', Blake2TimestampSigner, Blake2SerializerSigner)

# JSON valid types
JSONTypes = typing.Union[str, typing.Dict[str, typing.Any], int, float, typing.List[typing.Any]]

# Generic data type
TData = typing.TypeVar('TData', bound=JSONTypes)

# Cookie properties accepted by Starlette's `Response.set_cookie`, as a type
# Using a TypedDict proved to be too complicated and forced a very particular usage, so
# I opted for a simple dictionary.
CookieProperties = typing.Dict[str, typing.Union[str, bool, None]]

# Generic middleware type
TMiddleware = typing.TypeVar('TMiddleware')
