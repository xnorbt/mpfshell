##
# The MIT License (MIT)
#
# Copyright (c) 2016 Stefan Wendler
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
##

"""
2016-06-04, sw@kaltpost.de

Representation of a websocket/webrpel connection.

"""

import websocket
import threading
import time

from collections import deque
from mp.conbase import ConBase, ConError


class ConWebsock(ConBase, threading.Thread):

    def __init__(self, ip, password):

        ConBase.__init__(self)
        threading.Thread.__init__(self)

        self.daemon = True

        self.fifo = deque()

        websocket.enableTrace(False)
        self.ws = websocket.WebSocketApp("ws://%s:8266" % ip,
                                  on_message = self.on_message,
                                  on_error = self.on_error,
                                  on_close = self.on_close)

        self.start()

        self.timeout = 5.0

        if b'Password:' in self.read(256):
            self.ws.send(password + "\r")
            if not b'WebREPL connected' in self.read(256):
                raise ConError()
        else:
            raise ConError()

        self.timeout = 0.5

    def run(self):
        self.ws.run_forever()

    def __del__(self):
        self.close()

    def on_message(self, ws, message):
        self.fifo.extend(message)

    def on_error(self, ws, error):
        print("WS ERROR: %s" % error)

    def on_close(self, ws):
        pass

    def close(self):
        try:
            self.ws.close()
            self.join()
        except Exception:
            pass

    def read(self, size=1):

        data = ''

        tstart = time.time()

        while (len(data) < size) and (time.time() - tstart < self.timeout):
            if len(self.fifo) > 0:
                data += self.fifo.popleft()

        return data.encode("utf-8")

    def write(self, data):

        self.ws.send(data)
        return len(data)

    def inWaiting(self):
        return len(self.fifo)

    def survives_soft_reset(self):
        return False