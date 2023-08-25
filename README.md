# CoreFoundation based selector and asyncio event loop

## asyncio event loop

On macOS X, Cocoa uses an event loop to dispatch events ([`NSRunLoop`](https://developer.apple.com/documentation/foundation/nsrunloop), which is a wrapper around [`CFRunLoop`](https://developer.apple.com/documentation/corefoundation/cfrunloop?language=objc)).

Python's [asyncio](https://docs.python.org/3/library/asyncio.html) module uses an event loop too to handle asynchronous events. On macOS X, it's based on [kqueue](https://docs.python.org/3/library/selectors.html#selectors.KqueueSelector).

A thread can only use a single event loop, that's why it's not possible to use both Cocoa and asyncio on the same thread. This module implements an asyncio compatible event loop on top of CFRunLoop. Thus it's possible to use Cocoa in conjunction with asyncio.
It uses internally PyObjC's [`runEventLoop`](https://pyobjc.readthedocs.io/en/latest/api/module-PyObjCTools.AppHelper.html) or [`runConsoleEventLoop`](https://pyobjc.readthedocs.io/en/latest/api/module-PyObjCTools.AppHelper.html)

Here is an example video of a simple Cocoa based GUI using `asyncio` and `async`/`await` to handle subprocesses and network calls:

[![Example video](https://img.youtube.com/vi/-Arl0-7y7so/0.jpg)](https://www.youtube.com/watch?v=-Arl0-7y7so)

The corresponding code is here: [tests/gui/guidemo.py](https://github.com/alberthier/corefoundationasyncio/blob/master/tests/gui/guidemo.py)

Setup:

```python
    loop = CoreFoundationEventLoop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_forever()
    finally:
        loop.close()
```

`CoreFoundationEventLoop`'s constructor's first argument is a boolean. `True` for a console app, `False` (default) for a GUI app.
Additionnal arguments are then passed to [`PyObjCTools.AppHelper.runConsoleEventLoop`](https://pyobjc.readthedocs.io/en/latest/api/module-PyObjCTools.AppHelper.html) or [`PyObjCTools.AppHelper.runEventLoop`](https://pyobjc.readthedocs.io/en/latest/api/module-PyObjCTools.AppHelper.html)

## selector

This module also provides a [selector](https://docs.python.org/3/library/selectors.html) implementation based on [CFRunLoop](https://developer.apple.com/documentation/corefoundation/cfrunloop?language=objc). But his selector isn't compatible with Cocoa GUIs

## Installation

```shell
$ pip3 install corefoundationasyncio
```

This module depends on [pyobjc-framework-Cocoa](https://pypi.org/project/pyobjc-framework-Cocoa/)

## Contributing

Report issues [here](https://github.com/alberthier/corefoundationasyncio/issues)

Pull-requests welcome !

## License

This software is licensed under the [MIT](LICENSE) license
