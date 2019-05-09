import asyncio
from urllib.request import urlopen

from Cocoa import objc, NSWindowController, NSApplication, NSApp, NSPoint
from Foundation import NSObject

from corefoundationasyncio import CoreFoundationEventLoop


class GuiDemo(NSWindowController):
    textview = objc.IBOutlet()

    async def run_(self, cmd):
        proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()
        return stdout.decode() if proc.returncode == 0 else stderr.decode()

    async def request_(self, url):
        el = asyncio.get_event_loop()
        request = await el.run_in_executor(None, urlopen, url)
        return str(request.read(), 'utf-8')

    async def asynctask(self):
        txt = await self.run_('ls')
        self.appendText_(txt)
        await asyncio.sleep(2)
        txt = await self.run_('uname -a')
        self.appendText_(txt)
        await asyncio.sleep(2)
        txt = await self.request_('https://api.ipify.org')
        self.appendText_(txt)

    @objc.IBAction
    def syncop_(self, sender):
        self.appendText_('Sync text')

    @objc.IBAction
    def asyncop_(self, sender):
        asyncio.create_task(self.asynctask())

    @objc.IBAction
    def clear_(self, sender):
        self.textview.setString_('')

    def appendText_(self, text):
        old = self.textview.string()
        self.textview.setString_(old + text + '\n')
        self.textview.scrollToEndOfDocument_(None)


if __name__ == "__main__":
    app = NSApplication.sharedApplication()
    viewController = GuiDemo.alloc().initWithWindowNibName_("guidemo")
    viewController.showWindow_(viewController)
    NSApp.activateIgnoringOtherApps_(True)

    # Configure asyncio to use CoreFoundationEventLoop
    el = CoreFoundationEventLoop()
    asyncio.set_event_loop(el)
    el.run_forever()
