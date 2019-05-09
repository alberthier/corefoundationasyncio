#!/usr/bin/env python3

import sys
sys.path.append('..')

from corefoundationselector import CoreFoundationSelector
import asyncio
import os
import fcntl
from urllib.request import urlopen
import functools

async def test():
    print("waiting...")
    await asyncio.sleep(3)
    print("middle")
    await asyncio.sleep(2)
    print("done")

async def uname():
    await run('uname -a')

async def run(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()

    print(f'[{cmd!r} exited with {proc.returncode}]')
    if stdout:
        print(f'[stdout]\n{stdout.decode()}')
    if stderr:
        print(f'[stderr]\n{stderr.decode()}')

async def request(loop, url):
    request = await loop.run_in_executor(None, urlopen, url)
    return str(request.read())

async def net(loop):
    print('Requests')
    future1 = request(loop, 'http://www.google.com')
    future2 = request(loop, 'http://www.google.co.uk')
    response1 = await future1
    response2 = await future2
    print(response1)
    print(response2)

async def main(loop):
    print('Starting')

    ls = run('ls')
    goog = net(loop)

    await ls
    await goog

    print('Enter some text')

    # Make stdin non blocking
    orig_fl = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
    fcntl.fcntl(sys.stdin, fcntl.F_SETFL, orig_fl | os.O_NONBLOCK)

    reader = asyncio.StreamReader(loop=loop)
    reader_protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: reader_protocol, sys.stdin)
    # await asyncio.sleep(1)
    # print('.')
    # await asyncio.sleep(1)
    # print('.')
    # await asyncio.sleep(1)
    # print('.')
    while True:
        sys.stdout.flush()
        line = await reader.readline()
        if not line:  # EOF.
            break
        print('>> ' + str(line, 'utf-8'))
    print('Stopping')

el = asyncio.SelectorEventLoop(CoreFoundationSelector())
asyncio.set_event_loop(el)
#el.call_soon(test)
#el.run_until_complete(test())

el.create_task(uname())

el.run_until_complete(main(el))
#el.run_forever()
