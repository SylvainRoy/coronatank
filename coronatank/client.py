#!/usr/bin/env python3

"""
This file contains the TCP client used by the game to synchronize with the server.
"""


import socket

from collections import defaultdict

from . import Command
from . import Tank


class Client:
    """
    A TCP client to connect to the server and exchange tanks positions, angles, etc.
    """

    def __init__(self, ip, port, tanks):
        self.ip = ip
        self.port = port
        self.tanks = tanks
        assert(len(tanks) == 1)
        self.socket = None
        self.data = b''
        # The list of tanks controlled remotely
        self.remoteTanks = {}
        # The last received command from tanks controlled remotely
        self._lastCommandReceived = defaultdict(lambda: [])

    def connect(self):
        """
        Connect the client to the server in non-blocking mode.
        """
        # Connect to the server
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        err = self.socket.connect((self.ip, self.port))
        self.socket.setblocking(0)
        # Send ID request
        self.send_command(Command(state=Command.States.init))
        # Receive ID of the local tank
        while len(self.data) < Command.Msglen:
            self._recv_data(Command.Msglen - len(self.data))
        cmd = Command().decode(self.data[:Command.Msglen])
        self.data = self.data[Command.Msglen:]
        # Update the local tank
        assert(len(self.tanks) == 1)
        self.tanks[0].init_from_id(cmd.tankid)

    def recv_command(self, tankid):
        """
        Returns the last command or None.
        Called by remotePilots to get last command from the server.
        """
        if len(self._lastCommandReceived[tankid]) == 0:
            return None
        return self._lastCommandReceived[tankid].pop()

    def send_command(self, cmd):
        """
        Called by Pilots to transmit commands to the server.
        """
        self._send_data(cmd.encode())

    def synchronize(self):
        """
        Receives the commands from the server, executes or stores them.
        """
        # Read commands received from the server
        self._recv_data()
        while len(self.data) >= Command.Msglen:
            # Read a new command
            cmd = Command().decode(self.data[:Command.Msglen])
            self.data = self.data[Command.Msglen:]
            # Remove disconnected tank
            if cmd.state == Command.States.left:
                del(self.remoteTanks[cmd.tankid])
                del(self._lastCommandReceived[cmd.tankid])
            # Store received command, the RemotePilot will read it later
            else:
                # If this is a new tank, create and initialize it
                if cmd.tankid not in self.remoteTanks:
                    self.remoteTanks[cmd.tankid] = Tank().init_from_id(cmd.tankid)
                # Queue received command
                self._lastCommandReceived[cmd.tankid].insert(0, cmd)
        return list(self.remoteTanks.values())

    def _send_data(self, msg):
        """
        Internal method to send data to the server.
        """
        totalsent = 0
        while totalsent < len(msg):
            sent = self.socket.send(msg[totalsent:])
            if sent == 0:
                raise RuntimeError("Connection with server broken.")
            totalsent += sent

    def _recv_data(self, maxdata=128):
        """
        Internal method to recv data from the server.
        """
        try:
            data = self.socket.recv(maxdata)
            if data == b'':
                raise RuntimeError("Connection with server broken.")
        except BlockingIOError:
            data = b''
        self.data += data
