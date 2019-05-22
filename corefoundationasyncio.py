# -*- coding: utf-8 -*-

import asyncio
import sys
import threading

from CoreFoundation import (
    CFRunLoopGetCurrent,
    CFRunLoopTimerCreate, CFRunLoopAddTimer, CFRunLoopRemoveTimer, CFAbsoluteTimeGetCurrent,
    CFFileDescriptorCreate, CFFileDescriptorIsValid, CFFileDescriptorEnableCallBacks, CFFileDescriptorDisableCallBacks,
    CFFileDescriptorCreateRunLoopSource, CFRunLoopAddSource, CFRunLoopRemoveSource,
    kCFAllocatorDefault, kCFRunLoopDefaultMode, kCFRunLoopCommonModes,
    kCFFileDescriptorReadCallBack, kCFFileDescriptorWriteCallBack
)
import PyObjCTools.AppHelper

class _TimerHandle(asyncio.TimerHandle):

    def __init__(self, when, callback, args, loop, context):
        super().__init__(when, callback, args, loop, context)
        self.cf_runloop_timer = None


class _FDEntry:

    def __init__(self):
        self.cf_fd = None
        self.cf_source = None
        self.callbacks = {}


class CoreFoundationEventLoop(asyncio.SelectorEventLoop):
    """
    Event loop based on CoreFoundation's CFRunLoop.
    This allows integration of Cocoa GUI apps with asyncio
    """

    def __init__(self, console_app = False, *eventloop_args):
        self._console_app = console_app
        self._eventloop_args = eventloop_args
        self._registered_fds = {}
        self._runloop = CFRunLoopGetCurrent()
        super().__init__()

    # Running and stopping the event loop.

    def run_forever(self):
        """Run until stop() is called."""
        self._check_closed()
        if self.is_running():
            raise RuntimeError('This event loop is already running')
        if asyncio._get_running_loop() is not None:
            raise RuntimeError('Cannot run the event loop while another loop is running')
        self._set_coroutine_origin_tracking(self._debug)
        self._thread_id = threading.get_ident()

        old_agen_hooks = sys.get_asyncgen_hooks()
        sys.set_asyncgen_hooks(firstiter=self._asyncgen_firstiter_hook,
                               finalizer=self._asyncgen_finalizer_hook)
        try:
            asyncio._set_running_loop(self)
            if self._console_app:
                PyObjCTools.AppHelper.runConsoleEventLoop(*self._eventloop_args)
            else:
                PyObjCTools.AppHelper.runEventLoop(*self._eventloop_args)
        finally:
            self._thread_id = None
            asyncio._set_running_loop(None)
            self._set_coroutine_origin_tracking(False)
            sys.set_asyncgen_hooks(*old_agen_hooks)

    def _process_events(self, event_list):
        raise NotImplementedError("Not available in this implementation")

    def _run_once(self):
        raise NotImplementedError("Not available in this implementation")

    def stop(self):
        PyObjCTools.AppHelper.stopEventLoop()

    # Methods scheduling callbacks.  All these return Handles.

    def call_at(self, when, callback, *args, context=None):
        self._check_closed()
        if self._debug:
            self._check_thread()
            self._check_callback(callback, 'call_at')
        timerHandle = _TimerHandle(when, callback, args, self, context)
        if timerHandle._source_traceback:
            del timerHandle._source_traceback[-1]
        self._add_callback(timerHandle)
        return timerHandle

    def _call_soon(self, callback, args, context):
        handle = asyncio.Handle(callback, args, self, context)
        self._add_callback(handle)
        return handle

    def _add_callback(self, handle):
        assert isinstance(handle, asyncio.Handle), 'A Handle is required here'
        is_timer = isinstance(handle, _TimerHandle)
        if handle.cancelled():
            return
        def ontimeout(cf_timer, info):
            if not handle.cancelled():
                handle._run()
        when = handle.when() if is_timer else self.time()
        cf_timer = CFRunLoopTimerCreate(kCFAllocatorDefault, when, 0, 0, 0, ontimeout, None)
        CFRunLoopAddTimer(self._runloop, cf_timer, kCFRunLoopCommonModes)
        if is_timer:
            handle.cf_runloop_timer = cf_timer
            handle._scheduled = True

    def _timer_handle_cancelled(self, handle):
        CFRunLoopRemoveTimer(self._runloop, handle.cf_runloop_timer, kCFRunLoopCommonModes)

    def time(self):
        return CFAbsoluteTimeGetCurrent()

    # Ready-based callback registration methods.
    # The add_*() methods return None.
    # The remove_*() methods return True if something was removed,
    # False if there was nothing to delete.

    def _register_fd(self, fd, event, callback, args):
        entry = self._registered_fds.get(fd)
        if entry is not None:
            CFFileDescriptorEnableCallBacks(entry.cf_fd, event)
            entry.callbacks[event] = (callback, args)
        else:
            def fd_callback(file_desc, callback_types, entry):
                if callback_types & kCFFileDescriptorReadCallBack:
                    (callback, args) = entry.callbacks[kCFFileDescriptorReadCallBack]
                    callback(*args)
                if callback_types & kCFFileDescriptorWriteCallBack:
                    (callback, args) = entry.callbacks[kCFFileDescriptorWriteCallBack]
                    callback(*args)
                if CFFileDescriptorIsValid(file_desc):
                    CFFileDescriptorEnableCallBacks(file_desc, callback_types)

            entry = _FDEntry()
            entry.cf_fd = CFFileDescriptorCreate(kCFAllocatorDefault, fd, 0, fd_callback, entry)
            CFFileDescriptorEnableCallBacks(entry.cf_fd, event)
            entry.callbacks[event] = (callback, args)
            entry.cf_source = CFFileDescriptorCreateRunLoopSource(kCFAllocatorDefault, entry.cf_fd, 0)
            self._registered_fds[fd] = entry
            CFRunLoopAddSource(self._runloop, entry.cf_source, kCFRunLoopDefaultMode)

    def _unregister_fd(self, fd, event):
        entry = self._registered_fds.pop(fd, None)
        if entry is None:
            return False
        cb = entry.callbacks.pop(event, None)
        if cb is None:
            return False
        if len(entry.callbacks) != 0:
            CFFileDescriptorDisableCallBacks(entry.cf_fd, event)
        else:
            CFRunLoopRemoveSource(self._runloop, entry.cf_source, kCFRunLoopDefaultMode)
        return True

    def _add_reader(self, fd, callback, *args):
        self._check_closed()
        self._register_fd(fd, kCFFileDescriptorReadCallBack, callback, args)

    def _remove_reader(self, fd):
        if self.is_closed():
            return False
        return self._unregister_fd(fd, kCFFileDescriptorReadCallBack)

    def _add_writer(self, fd, callback, *args):
        self._check_closed()
        self._register_fd(fd, kCFFileDescriptorWriteCallBack, callback, args)

    def _remove_writer(self, fd):
        if self.is_closed():
            return False
        return self._unregister_fd(fd, kCFFileDescriptorWriteCallBack)
