#!/usr/bin/env python3

"""
Basic tpc server that forward messages received from any client to all the others.
"""


from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import asyncio
import struct
import argparse

from command import Command


# Store the transport of each client.
Clients = {}

# Store the last message sent to each client.
LastMessages = {}


class TankServerProtocol(asyncio.Protocol):

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
        print('Connection from {} got assigned ID {}'.format(transport.get_extra_info('peername'), self._id))
        # Assign and communicate ID to the newly connected tank.
        transport.write(Command(tankid=self._id).encode())
        # Communicate positions of the other tanks to the newly connected tank.
        for _id, msg in LastMessages.items():
            transport.write(msg)

    def connection_lost(self, exc):
        """
        Remove the disconected client from the list of active clients.
        """
        global Clients, LastMessages
        # The client disconnected, remove it from the list
        print('Client {} disconnected.'.format(self._id))
        del(Clients[self._id])
        if self._id in LastMessages.keys():
            del(LastMessages[self._id])
        # Warn all the other clients
        msg = Command(tankid=self._id, state=Command.States.left).encode()
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

    # Parsing command line
    parser = argparse.ArgumentParser()
    parser.add_argument("--listen", help="IP:port of the server", required=True)
    args = parser.parse_args()
    if args.listen:
        ip, port = args.listen.split(":")
        port = int(port)

    # Launch server
    loop = asyncio.get_running_loop()
    server = await loop.create_server(lambda: TankServerProtocol(), ip, port)
    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    asyncio.run(main())
