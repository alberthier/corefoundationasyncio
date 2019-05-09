# CoreFoundation based selector and asyncio event loop

## asyncio event loop

Cocoa and asyncio need to use the same event loop to be usable in the same thread.
The `corefoundationasyncio` provides an `asyncio` event loop based on CoreFoundation (Cocoa's event loop)

## selector
