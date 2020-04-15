#!/usr/bin/env python3

"""
Basic tpc server that forward messages received from any client to all the others.
"""


import asyncio
import struct

from resources import Command
from config import CONFIG


# Store the transport of each client.
Clients = {}

# Store the last message sent to each client.
LastMessages = {}


class EchoServerProtocol(asyncio.Protocol):

    def __init__(self):
        self.buffer = b''

    def connection_made(self, transport):
        """
        Accept cxn of new client, assign them an ID.
        """
        global Clients, LastMessages
        # Determine ID of the newly connected client
        self._id = min(range(len(Clients)+1) - Clients.keys())
        Clients[self._id] = transport
        print('Connection from {} got assigned ID {}'.format(
            transport.get_extra_info('peername'),
            self._id))
        # Assign and communicate ID, position and angle to the newly connected tank.
        tankConfig = CONFIG["tanks"][self._id]
        cmd = Command(_id=self._id, position=tankConfig["position"], angle=tankConfig["angle"])
        transport.write(cmd.encode())
        # Communicate last position of the other tanks to the newly connected tank.
        for _id, msg in LastMessages.items():
            transport.write(msg)

    def connection_lost(self, exc):
        """
        Remove the disconected client from the list of active clients.
        """
        global Clients, LastMessages
        # The client disconnected, remove it from the list
        del(Clients[self._id])
        del(LastMessages[self._id])
        # Warn all the other clients
        msg = Command(_id=self._id, state=Command.State.left).encode()
        for _id, transport in Clients.items():
            if _id != self._id:
                transport.write(msg)

    def data_received(self, data):
        """
        Receive message from one client and forward to all others.
        """
        global Clients, LastMessages
        self.buffer += data
        while len(self.buffer) >= Command.Msglen:
            msg = self.buffer[:Command.Msglen]
            LastMessages[self._id] = msg
            for _id, transport in Clients.items():
                if _id != self._id:
                    transport.write(msg)
            self.buffer = self.buffer[Command.Msglen:]


async def main():
    loop = asyncio.get_running_loop()
    server = await loop.create_server(lambda: EchoServerProtocol(), '127.0.0.1', 8888)
    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    asyncio.run(main())
