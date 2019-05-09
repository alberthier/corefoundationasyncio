# -*- coding: utf-8 -*-

from selectors import (
    BaseSelector, SelectorKey,
    EVENT_READ, EVENT_WRITE
)

from CoreFoundation import (
    CFFileDescriptorCreate, CFFileDescriptorIsValid, CFFileDescriptorDisableCallBacks, CFFileDescriptorEnableCallBacks, CFFileDescriptorCreateRunLoopSource,
    CFRunLoopRunInMode, CFRunLoopStop, CFRunLoopGetCurrent, CFRunLoopAddSource, CFRunLoopRemoveSource,
    kCFRunLoopDefaultMode, kCFAllocatorDefault, kCFRunLoopCommonModes
)

class _FDEntry:

    def __init__(self):
        self.cf_fd = None
        self.cf_source = None


class CoreFoundationSelector(BaseSelector):

    def __init__(self):
        super().__init__()
        self._runloop = CFRunLoopGetCurrent()
        self._mappings = {}
        self._registered_fds = {}
        self._triggered_descriptors = []
        self._fd_events_to_enable = {}

    def register(self, fileobj, events, data=None):
        fileno = fileobj if isinstance(fileobj, int) else fileobj.fileno()
        key = SelectorKey(fileobj, fileno, events, data)
        self._mappings[fileobj] = key

        entry = _FDEntry()
        entry.cf_fd = CFFileDescriptorCreate(kCFAllocatorDefault, fileno, 0, self._fdCallback, key)
        self._fd_events_to_enable[entry.cf_fd] = events
        entry.cf_source = CFFileDescriptorCreateRunLoopSource(kCFAllocatorDefault, entry.cf_fd, 0)
        CFRunLoopAddSource(self._runloop, entry.cf_source, kCFRunLoopCommonModes)
        self._registered_fds[fileobj] = entry

    def unregister(self, fileobj):
        del self._mappings[fileobj]
        source = self._registered_fds.pop(fileobj).cf_source
        CFRunLoopRemoveSource(self._runloop, source, kCFRunLoopCommonModes)

    def modify(self, fileobj, events, data=None):
        entry = self._registered_fds.get(fileobj, None)
        if entry and CFFileDescriptorIsValid(entry.cf_fd):
            self._fd_events_to_enable[entry.cf_fd] = events

    def select(self, timeout=None):
        if timeout is None:
            timeout = 24 * 3600
        for cf_fd, events in self._fd_events_to_enable.items():
            CFFileDescriptorDisableCallBacks(cf_fd, ~events)
            CFFileDescriptorEnableCallBacks(cf_fd, events)
        self._fd_events_to_enable = {}
        result = CFRunLoopRunInMode(kCFRunLoopDefaultMode, timeout, True)
        ret = self._triggered_descriptors
        self._triggered_descriptors = []
        return ret

    def close(self):
        CFRunLoopStop(self._runloop)

    def get_map(self):
        return self._mappings

    def _fdCallback(self, fileDescriptor, callBackTypes, key):
        self._triggered_descriptors.append((key, callBackTypes))
        self._fd_events_to_enable[fileDescriptor] = callBackTypes
