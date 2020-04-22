#!/usr/bin/env python3

"""
This file contains the command class.
"""

import struct

from enum import Enum

from . import Config


class Command:
    """
    A command produced by a pilot and executed by a tank.
    Possibly exchanged over the network.
    """

    Format = 'i'*9
    Msglen = struct.calcsize(Format)
    States = Enum("States", "init operational destroyed left")

    def __init__(self, tankid=None, state=None, angle=None, speed=None,
                 position=None, turretangle=None, fire=None, touchedby=None):
        self.tankid = tankid
        self.state = state
        self.angle = angle
        self.speed = speed
        self.position = position
        if self.position is not None:
            self.position = tuple((position[i] % Config.screen[i] for i in range(2)))
        self.turretangle = turretangle
        self.fire = fire
        self.touchedby = touchedby
        assert((self.touchedby is None) or (type(self.touchedby) == int))

    def encode(self):
        tankid = self.tankid if self.tankid is not None else -1
        state = self.state.value if self.state is not None else -1
        angle = self.angle if self.angle is not None else Config.maxInt
        speed = self.speed if self.speed is not None else Config.maxInt
        x, y = self.position if self.position is not None else (-1, -1)
        turretangle = self.turretangle if self.turretangle is not None else Config.maxInt
        fire = self.fire if self.fire is not None else -1
        touchedby = self.touchedby if self.touchedby is not None else -1
        return struct.pack(self.Format,
                           tankid, state, angle, speed, x, y, turretangle, fire, touchedby)

    def decode(self, data):
        tankid, state, angle, speed, x, y, turretangle, fire, touchedby = struct.unpack(self.Format, data)
        self.tankid = tankid if tankid != -1 else None
        self.state = self.States(state) if state != -1 else None
        self.angle = angle if angle != Config.maxInt else None
        self.speed = speed if speed != Config.maxInt else None
        self.position = (x, y) if x != -1 else None
        self.turretangle = turretangle if turretangle != Config.maxInt else None
        self.fire = fire if fire != -1 else None
        self.touchedby = touchedby if touchedby != -1 else None
        return self

    def __repr__(self):
        return "<Cmd {} {} {} {} {} {} {} {}>".format(self.tankid, self.state, self.angle, self.speed,
                                                  self.position, self.turretangle, self.fire, self.touchedby)
