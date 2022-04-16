# Changelog

# 0.2.0 - 2022-04-14

**Changed**

* BREAKING CHANGE: Cookie data is now set in the state as the [CookieData](cookie.md#asgi_signing_middleware.cookie.CookieData) object, which also holds any exception thrown by Blake2Signer. This is breaking because any previous implementation has to be adapted to use this new object.
* When the cookie is empty, the middleware's `unsign` method is no longer called, and state data is set to null. Previously, it was called with an empty string causing an exception, which set the state data to null, so the outcome remains the same.
* If the new state data is null, the cookie won't be written. To overwrite an existing cookie with empty data, just use an empty value instead (empty string, empty dict, etc). This hasn't actually changed, so this is just a clarification on how it was already working.

**Security**

* Implement [`minisign`](https://jedisct1.github.io/minisign/) to sign all release packages, and tags (using [`git-minisign`](https://gitlab.com/hackancuba/git-minisign)), instead of [`gpg`](https://gist.github.com/HacKanCuBa/afe0073fe35fddf01642220acd4cde17).

## 0.1.2 - 2022-01-23

**Added**

* Add tests and docs for Starlite.

## 0.1.1 - 2022-01-20

**Added**

- Initial release as a [package](https://pypi.org/project/asgi-signing-middleware/).

**Changed**

- Refactor tests for pytest.

## 0.1.0 - 2022-01-17

**Added**

- Initial release as a [snippet](https://gitlab.com/hackancuba/blake2signer/-/snippets/2236491).
