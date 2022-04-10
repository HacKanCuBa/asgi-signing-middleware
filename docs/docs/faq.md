# FAQ

## Is this project being maintained?

Yes, I'm actively maintaining it, and producing releases on a regular basis, even with new features. As a general rule, you can check the [repo activity](https://gitlab.com/hackancuba/asgi-signing-middleware/activity) or the [commits graph](https://gitlab.com/hackancuba/asgi-signing-middleware/-/network/develop).

## How can I do *something*?

Check the [examples](examples.md) for more information. If you still can't solve your doubt, please [open an issue](https://gitlab.com/hackancuba/asgi-signing-middleware/-/issues/new).

## Can I use this package in production?

No, it is still very early in development. Stability and api is not ensured and may change from version to version. However, it is so simple right now that you could get away with pinning the version and using it as it is. 

## Has this package been audited?

No, not yet. I will look for it once it reaches a stable version.

## Why isn't Python 3.7 supported?

Some things didn't work in Python 3.7, as the hack to get a base type in a `Generic` class (`typing.get_args(type(self).__orig_bases__[0])[0]`). And given that it's already quite old, and even PyPy and Stackless already upgraded to 3.8, I decided to not support it in the first place.
