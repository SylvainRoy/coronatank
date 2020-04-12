#!/usr/bin/env python3

"""
A dummy tcp client whose sole purpose is to test the game tcp server.
"""

import asyncio
import time

from tools import encode_message, decode_message, MSGLEN


MESSAGES = [(0,1,2,3),
            (5,6,7,8)]


class EchoClientProtocol(asyncio.Protocol):

    def __init__(self, on_con_lost):
        self.clientId = None
        self.on_con_lost = on_con_lost
        self.buffer = b''

    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        self.buffer += data
        while len(self.buffer) >= MSGLEN:
            m = decode_message(self.buffer[:MSGLEN])
            # The first message received is the client ID
            if self.clientId is None:
                self.clientId = m[0]
                print("ClientId: ", self.clientId)
                self.send()
            else:
                print("Msg recv: ", m)
            self.buffer = self.buffer[MSGLEN:]

    def connection_lost(self, exc):
        print('The server closed the connection')
        self.on_con_lost.set_result(True)

    def send(self):
        for msg in MESSAGES:
            msgdata = encode_message(*msg)
            self.transport.write(msgdata)
            print("Msg sent: {}".format(msg))


async def main():
    loop = asyncio.get_running_loop()
    on_con_lost = loop.create_future()

    transport, protocol = await loop.create_connection(
        lambda: EchoClientProtocol(on_con_lost),
        '127.0.0.1', 8888)

    # Wait until the protocol signals that the connection
    # is lost and close the transport.
    try:
        await on_con_lost
    finally:
        transport.close()


asyncio.run(main())
