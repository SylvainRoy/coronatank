#!/usr/bin/env python3

"""
This file contains all the main class of the game: tanks, turret, walls, etc.
"""

import pygame
import socket
import time
import struct

from collections import defaultdict
from math import cos, sin, sqrt, radians, copysign
from enum import Enum
from collections import namedtuple
from random import randint

from config import Config


class Tank:
    """
    A vehicule which can move, fire, collide with walls.
    It requires a turret and a pilot.
    """

    def __init__(self, position=None, angle=None, color=None, turret=None, pilot=None):
        self._id = None
        if position:
            self.position = tuple((position[j] % Config.screen[j] for j in range(2)))
        else:
            self.position = None
        self.angle = angle
        self.color = color
        self.speed = 0
        if turret is None:
            self.turret = Turret()
        else:
            self.turret = turret
        self.turret.tank = self
        if pilot is None:
            self.pilot = RemotePilot()
        else:
            self.pilot = pilot
        self.fire = False
        self.destroyedUntil = None
        self.touchedby = None

    def init_from_id(self, tankid):
        """
        Updates the tank once it got an ID assinged by the server.
        """
        self._id = tankid
        self.position = tuple((Config.tanks[tankid]["position"][i] % Config.screen[i]
                               for i in range(2)))
        self.angle = Config.tanks[tankid]["angle"]
        self.color = Config.tanks[tankid]["color"]
        return self

    def draw(self, screen):
        """
        Draws the tank.
        """
        surface = pygame.Surface(Config.tankDimensions).convert_alpha()
        surface.fill((0,0,0,0))
        # Draw the body of the tank
        pygame.draw.rect(surface, self.color, pygame.Rect((0,0), Config.tankDimensions))
        # Draw the caterpillars
        pygame.draw.rect(surface, (255,255,255,255),
                         pygame.Rect((0,0),
                                     (Config.tankDimensions[0], Config.tankDimensions[1]//6)))
        pygame.draw.rect(surface, (255,255,255,255),
                         pygame.Rect((0, 5*Config.tankDimensions[1]//6 + 1),
                                     Config.tankDimensions))
        # Draw the turret
        self.turret.draw(surface)
        # Rotate the tank
        surface = pygame.transform.rotate(surface, self.angle)
        centerX, centerY = surface.get_rect().center
        x, y = self.position[0] - centerX, self.position[1] - centerY
        # Display the tank
        screen.blit(surface, (x,y))

    def update(self, events, pressed, projectiles, walls, tanks, client):
        """
        Updates the state of the tank based on the pilot's command.
        """
        # Get instructions from pilot
        cmd = self.pilot.update(self, events, pressed, projectiles, walls, client)
        if cmd is None:
            return
        assert(self._id == cmd.tankid)
        # Update the tank accordingly
        if cmd.state == Command.States.destroyed:
            self.destroy()
        elif cmd.state == Command.States.operational:
            self.repair()
        if cmd.angle is not None:
            self.angle = cmd.angle
        if cmd.speed is not None:
            self.speed = cmd.speed
        if cmd.position is not None:
            self.position = cmd.position
        if cmd.turretangle is not None:
            self.turret.angle = cmd.turretangle
        if cmd.fire is not None:
            self.turret.fire(projectiles, cmd.fire)
        if cmd.touchedby is not None:
            projectiles[cmd.touchedby].trigger()

    def detect_collision(self, position, walls):
        """
        Detects collisions with walls at position.
        """
        innerrect = self.get_inner_rect(position)
        wallrects = [w.rect for w in walls]
        indices = innerrect.collidelistall(wallrects)
        return len(indices) != 0

    def detect_hit(self, projectiles):
        """
        Detects hits by projectiles.
        Returns a projectile or None.
        """
        tankrect = self.get_avg_rect()
        for projectile in projectiles.values():
            # A tank cannot destroy itself
            if projectile.tank == self:
                continue
            if tankrect.collidepoint(projectile.position):
                return projectile
        return None

    def get_inner_rect(self, position=None):
        """
        Returns an inner rectangle of the tank to use for wall collision detection.
        """
        if position is None:
            position = self.position
        innersize = min(Config.tankDimensions) - 2 * Config.wallThickness
        return pygame.Rect((position[0] - innersize//2, position[1] - innersize//2),
                           (innersize, innersize))

    def get_avg_rect(self, position=None):
        """
        Returns a rectangle of the tank to use for projectile collision detection.
        """
        if position is None:
            position = self.position
        avgsize = (Config.tankDimensions[0] + Config.tankDimensions[1]) // 2
        return pygame.Rect((position[0] - avgsize//2, position[1] - avgsize//2),
                           (avgsize, avgsize))

    def destroy(self):
        """
        Destroys the tank.
        """
        if self.destroyedUntil is None:
            self.speed = 0
            self.alivecolor = self.color
            self.color = (30, 30, 30)
            self.destroyedUntil = time.time() + Config.tankDeathDuration

    def repair(self):
        """
        Repairs the tank.
        """
        if self.destroyedUntil is not None:
            self.color = self.alivecolor
            self.destroyedUntil = None

    def __repr__(self):
        return "<Tank {} {} {}>".format(self._id, self.position, self.angle)


class Turret:
    """
    The turrets that seats on top of the tanks.
    """

    def __init__(self):
        self.angle = 0
        self.color = Config.turretColor
        self.tank = None
        self.centerX = Config.tankDimensions[0] // 2
        self.centerY = Config.tankDimensions[1] // 2
        self.canonLen = min(Config.tankDimensions) // 2
        self.radius = self.canonLen // 2

    def draw(self, surface):
        """
        Draws the turret.
        """
        # Draw the turret
        pygame.draw.circle(surface, self.color, (self.centerX, self.centerY), self.radius)
        # Draw the canon
        canonEndX = self.centerX + cos(radians(self.angle)) * self.canonLen
        canonEndY = self.centerY - sin(radians(self.angle)) * self.canonLen
        pygame.draw.line(surface, self.color, (self.centerX, self.centerY), (canonEndX, canonEndY), 4)

    def fire(self, projectiles, projectileid):
        """
        Fires a new projectile.
        """
        angle = self.tank.angle + self.angle
        aX = int(self.tank.position[0] + self.canonLen * cos(radians(angle)))
        aY = int(self.tank.position[1] - self.canonLen * sin(radians(angle)))
        projectile = Amunition(projectileid, (aX, aY), angle, self.tank)
        projectiles[projectileid] = projectile
        return projectile


class Amunition:
    """
    The projectiles fired by the tank.
    """

    States = Enum('States', 'active triggered detonated')
    _Counter = 1000 * randint(1, 1000)

    def __init__(self, _id, position, angle, tank):
        self._id = _id
        self.position = position
        self.angle = angle
        self.speed = 10
        self.tank = tank
        self.state = self.States.active

    def next_id():
        Amunition._Counter += 1
        return Amunition._Counter

    def draw(self, screen):
        """
        Draws the projectile.
        """
        if self.state == self.States.active:
            pygame.draw.circle(screen, (0,0,0,255), self.position, 3)
        elif self.state == self.States.triggered:
            pygame.draw.circle(screen, (0,0,0,255), self.position, 30)
            self.state = self.state.detonated

    def update(self, events, pressed, projectiles, walls, tanks, client):
        """
        Updates the state of the projectile.
        """
        # Move the projectile off the screen if detonated, it'll get it removed
        if self.state == self.States.detonated:
            self.position = (-10, -10)
            self.angle = 180
            self.speed = 10
            return
        # Update position
        dx = int(self.speed * cos(radians(self.angle)))
        dy = int(self.speed * -sin(radians(self.angle)))
        x, y = self.position
        self.position = (x + dx, y + dy)
        # Detect collision with a wall
        # (Collision with tanks are detected by the Pilot)
        for wall in walls:
            if wall.rect.collidepoint(self.position):
                self.trigger()
                return

    def trigger(self):
        """
        Trigger the explosion of the projectile.
        """
        self.state = self.States.triggered


class Wall:
    """
    The walls of the battlefield.
    """

    def __init__(self, beg, end):
        assert(beg[0] <= end[0])
        assert(beg[1] <= end[1])
        self.beg = beg
        self.end = end
        thickness = Config.wallThickness
        self.rect = pygame.Rect((beg[0]-thickness, beg[1]-thickness),
                                (end[0]-beg[0]+2*thickness, end[1]-beg[1]+2*thickness))

    def draw(self, screen):
        """
        Draws the wall.
        """
        pygame.draw.line(screen, Config.wallColor, self.beg, self.end, 4)

    def draw_rect(self, screen):
        """
        Draws the rectangle used for collision detection.
        """
        pygame.draw.rect(screen, (0,0,0), self.rect, 1)


class Command:
    """
    A command produced by a pilot and executed by a tank.
    Possibly exchanged over the network.
    """

    Format = 'i'*9
    Msglen = struct.calcsize(Format)
    # todo: should be States
    States = Enum("State", "operational destroyed left")

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


class Pilot:
    """
    A basic pilot that drives a tank based on the player's input.
    This class should be 'stateless'.
    """

    def __init__(self, keymap):
        self.forward = keymap["forward"]
        self.backward = keymap["backward"]
        self.left = keymap["left"]
        self.right = keymap["right"]
        self.turretRight = keymap["turretRight"]
        self.turretLeft = keymap["turretLeft"]
        self.fire = keymap["fire"]

    def update(self, tank, events, pressed, projectiles, walls, client):
        """
        Build next command, send it to the server (for remote tanks) and return it (for local tank).
        """
        cmd = self.command(tank, events, pressed, projectiles, walls)
        if client and cmd:
            client.send_command(cmd)
        return cmd

    def command(self, tank, events, pressed, projectiles, walls):
        """
        Return a command to be executed by the local and remote tanks, None if nothing to do.
        """
        # No move if the tank is destroyed
        if tank.destroyedUntil:
            if time.time() < tank.destroyedUntil:
                return None
            else:
                return Command(tankid=tank._id, state=Command.States.operational)

        # Detect collisions with projectiles
        projectile = tank.detect_hit(projectiles)
        if projectile is not None:
            return Command(tankid=tank._id, speed=0, state=Command.States.destroyed, touchedby=projectile._id)

        # Compute new tank angle based on player's input
        rotation = Config.tankDeltaAngle * (pressed[self.left] - pressed[self.right])
        newtankangle = tank.angle + rotation

        # Update tank speed based on player's input
        translation = pressed[self.forward] - pressed[self.backward]
        if translation != 0:
            newtankspeed = max(-Config.tankMaxSpeed, min(Config.tankMaxSpeed, tank.speed + translation))
        elif tank.speed != 0:
            # Progressively stop the tank if no input from the player
            newtankspeed = copysign(abs(tank.speed)-1, tank.speed)
        else:
            newtankspeed = 0
        newtankspeed = int(newtankspeed)

        # Compute move considering possible collision with walls
        delta = newtankspeed
        direction = copysign(1, delta)
        while True:
            # Compute tentative position
            dx = delta * cos(radians(newtankangle))
            dy = delta * -sin(radians(newtankangle))
            x, y = tank.position
            newtankposition = (int(x + dx), int(y + dy))
            # Reduce move in case of collision
            if tank.detect_collision(newtankposition, walls):
                delta -= direction
                newtankspeed = 0
            else:
                break

        # Compute turret angle based on player's input
        rotation = Config.turretDeltaAngle * (pressed[self.turretLeft] - pressed[self.turretRight])
        newturretangle = tank.turret.angle + rotation

        # Fire a new projectile
        fire = None
        if any((e.type == pygame.KEYUP and e.key == self.fire for e in events)):
            fire = Amunition.next_id()

        assert(type(newtankangle) == int)
        assert(type(newtankspeed) == int)
        assert(type(newtankposition[0]) == int)
        assert(type(newtankposition[1]) == int)
        assert(type(newturretangle) == int)

        return Command(tankid=tank._id, angle=newtankangle, speed=newtankspeed,
                       position=newtankposition, turretangle=newturretangle, fire=fire)


class RemotePilot:
    """
    A "dummy' pilot which returns the command from the server.
    This class should be 'stateless'.
    """

    def update(self, tank, events, pressed, projectiles, walls, client):
        """
        Collects last command from the server and return it to the tank.
        """
        cmd = client.recv_command(tank._id)
        return cmd

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
        # todo: Should be a queue?
        self._lastCommandReceived = defaultdict(lambda: [])

    def connect(self):
        """
        Connect the client to the server in non-blocking mode.
        """
        # Connect to the server
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        err = self.socket.connect(('127.0.0.1', 8888))
        self.socket.setblocking(0)
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
