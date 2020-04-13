#!/usr/bin/env python3

"""
Basic tpc server that forward messages received from any client to all the others.
"""


import asyncio
import struct

from tools import encode_message, decode_message, MSGLEN
from config import CONFIG


Clients = {}


class EchoServerProtocol(asyncio.Protocol):

    def __init__(self):
        self.buffer = b''

    def connection_made(self, transport):
        global Clients
        self.clientId = min(range(len(Clients)+1) - Clients.keys())
        tankConfig = CONFIG["tanks"][self.clientId]
        x, y = tankConfig["position"]
        angle = tankConfig["angle"]
        Clients[self.clientId] = transport
        transport.write(encode_message(self.clientId, x, y, angle, 0, 0))
        print('Connection from {} got assigned ID {}'.format(
            transport.get_extra_info('peername'),
            self.clientId))

    def connection_lost(self, exc):
        del(Clients[self.clientId])

    def data_received(self, data):
        global Clients
        self.buffer += data
        while len(self.buffer) >= MSGLEN:
            for clientid, transport in Clients.items():
                if clientid != self.clientId:
                    #print("{} => {}: {}".format(self.clientId, clientid, decode_message(self.buffer[:MSGLEN])))
                    transport.write(self.buffer[:MSGLEN])
            self.buffer = self.buffer[MSGLEN:]


async def main():
    loop = asyncio.get_running_loop()
    server = await loop.create_server(lambda: EchoServerProtocol(), '127.0.0.1', 8888)
    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    asyncio.run(main())
