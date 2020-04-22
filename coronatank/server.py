#!/usr/bin/env python3

"""
Basic tpc server that forward messages received from any client to all the others.
"""


from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import asyncio
import struct
import argparse

from . import Command


# Store the transport of each client.
Clients = {}

# Store the last message sent to each client.
LastMessages = {}


class TankServerProtocol(asyncio.Protocol):

    def __init__(self):
        self.buffer = b''
        self._id = None
        self.transport = None

    def connection_made(self, transport):
        """
        Accept cxn of new client, assign them an ID.
        """
        print('New connection from {}'.format(transport.get_extra_info('peername')))
        self.transport = transport

    def data_received(self, data):
        """
        Receive message from one client and forward to all others.
        """
        global Clients, LastMessages
        self.buffer += data
        while len(self.buffer) >= Command.Msglen:

            # Read next message
            msg = self.buffer[:Command.Msglen]
            self.buffer = self.buffer[Command.Msglen:]

            # The first message received should be an init request
            if self._id is None and Command().decode(msg).state == Command.States.init:
                # Determine the ID of the newly connected client
                self._id = min(range(len(Clients)+1) - Clients.keys())
                Clients[self._id] = self.transport
                print("{} got assigned ID '{}'".format(self.transport.get_extra_info('peername'),
                                                     self._id))
                # Communicate ID to the newly connected tank.
                self.transport.write(Command(tankid=self._id).encode())
                # Communicate positions of the other tanks to the newly connected tank.
                for _id, msg in LastMessages.items():
                    self.transport.write(msg)

            # Later messages received are tank updates to transmit to all other tanks
            else:
                LastMessages[self._id] = msg
                for _id, transport in Clients.items():
                    if _id != self._id:
                        transport.write(msg)

    def connection_lost(self, exc):
        """
        Remove the disconected client from the list of active clients.
        """
        global Clients, LastMessages
        # The client disconnected, remove it from the list
        print("Client '{}' disconnected.".format(self._id))
        if self._id in Clients.keys():
            del(Clients[self._id])
        if self._id in LastMessages.keys():
            del(LastMessages[self._id])
        # Warn all the other clients
        if self._id is not None:
            msg = Command(tankid=self._id, state=Command.States.left).encode()
            for _id, transport in Clients.items():
                if _id != self._id:
                    transport.write(msg)


async def runserver():

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


def server():
    asyncio.run(runserver())


if __name__ == '__main__':
    server()
