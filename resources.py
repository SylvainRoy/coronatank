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
from config import Config


class Tank:
    """
    A vehicule which can move, fire, collide with walls.
    It requires a turret and a pilot.
    """

    def __init__(self, position, angle, color, turret, pilot):
        self._id = None
        self.position = tuple((position[j] % Config.screen[j] for j in range(2)))
        self.angle = angle
        self.color = color
        self.speed = 0
        self.turret = turret
        self.turret.tank = self
        self.pilot = pilot
        self.fire = False
        self.destroyedUntil = None

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

    def update(self, events, pressed, projectiles, walls, tanks):
        """
        Updates the state of the tank based on player's input and game state.
        """
        # Get instructions from pilot
        cmd = self.pilot.update(self, events, pressed, projectiles, walls)
        # Update the tank accordingly
        self.angle = cmd.angle
        self.speed = cmd.speed
        self.position = cmd.position
        self.turret.angle = cmd.turretangle
        self.fire = cmd.fire
        if (cmd.state == Command.State.destroyed) and (self.destroyedUntil is None):
            self.destroy()
        if (cmd.state == Command.State.operational) and (self.destroyedUntil is not None):
            self.repair()
        if self.fire:
            self.turret.fire(projectiles)

    def detect_collision(self, position, walls):
        """
        Detects collision with walls at position.
        """
        innerrect = self.get_inner_rect(position)
        wallrects = [w.rect for w in walls]
        indices = innerrect.collidelistall(wallrects)
        return len(indices) != 0

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
        self.color = self.alivecolor
        self.destroyedUntil = None


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

    def fire(self, projectiles):
        """
        Fires a new projectile.
        """
        angle = self.tank.angle + self.angle
        aX = int(self.tank.position[0] + self.canonLen * cos(radians(angle)))
        aY = int(self.tank.position[1] - self.canonLen * sin(radians(angle)))
        projectiles.append(Amunition((aX, aY), angle, self.tank))


class Amunition:
    """
    The projectiles fired by the tank.
    """

    States = Enum('States', 'active detonated destroyed')

    def __init__(self, position, angle, tank):
        self.position = position
        self.angle = angle
        self.speed = 10
        self.tank = tank
        self.state = self.States.active

    def draw(self, screen):
        """
        Draws the projectile.
        """
        if self.state == self.States.active:
            pygame.draw.circle(screen, (0,0,0,255), self.position, 3)
        elif self.state == self.States.detonated:
            pygame.draw.circle(screen, (0,0,0,255), self.position, 30)

    def update(self, events, pressed, projectiles, walls, tanks):
        """
        Updates the state of the projectile.
        """
        # Move the projectile off the screen if detonated, it'll get it removed
        if self.state == self.States.detonated:
            self.state = self.States.destroyed
            self.position = (-1000, -1000)
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
                self.state = self.States.detonated
        # # Detect collision with a tank
        # for tank in tanks:
        #     if tank.get_avg_rect().collidepoint(self.position):
        #         self.state = self.States.detonated
        #         tank.destroy()


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

    Format = 'i'*7
    Msglen = struct.calcsize(Format)
    State = Enum("State", "operational destroyed left")

    def __init__(self, _id=None, state=State.operational, angle=0, speed=0, position=(0,0), turretangle=0, fire=False):
        self._id = _id
        self.state = state
        self.angle = angle
        self.speed = speed
        self.position = tuple((position[i] % Config.screen[i] for i in range(2)))
        self.turretangle = turretangle
        self.fire = fire

    def encode(self):
        x, y = self.position
        fire = int(self.fire)
        state = self.state.value
        return struct.pack('i'*7, self._id, state, self.angle, x, y, self.turretangle, fire)

    def decode(self, data):
        self._id, state, self.angle, x, y, self.turretangle, fire = struct.unpack('i'*7, data)
        self.state = self.State(state)
        self.position = (x, y)
        self.fire = (fire == 1)
        return self

    def copy_from_tank(self, tank):
        self._id = tank._id
        if tank.destroyedUntil is None:
            self.state = self.State.operational
        else:
            self.state = self.State.destroyed
        self.angle = tank.angle
        self.speed = tank.speed
        self.position = tank.position
        self.turretangle = tank.turret.angle
        self.fire = tank.fire
        return self


class Pilot:
    """
    A basic pilot that drives the tank based on the player's input.
    """

    def __init__(self, keymap):
        self.forward = keymap["forward"]
        self.backward = keymap["backward"]
        self.left = keymap["left"]
        self.right = keymap["right"]
        self.turretRight = keymap["turretRight"]
        self.turretLeft = keymap["turretLeft"]
        self.fire = keymap["fire"]

    def update(self, tank, events, pressed, projectiles, walls):

        # Detect collisions with projectiles
        tankrect = tank.get_avg_rect()
        for projectile in projectiles:
            if projectile.tank == tank:
                continue
            if tankrect.collidepoint(projectile.position):
                projectile.state = Amunition.States.detonated
                return Command(angle=tank.angle, speed=0, position=tank.position,
                               turretangle=tank.turret.angle, fire=False, state=Command.State.destroyed)

        # No move if the tank is destroyed
        if tank.destroyedUntil and time.time() < tank.destroyedUntil:
            return Command(angle=tank.angle, speed=0, position=tank.position,
                           turretangle=tank.turret.angle, fire=False, state=Command.State.destroyed)

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
        fire = False
        if any((e.type == pygame.KEYUP and e.key == self.fire for e in events)):
            fire = True

        assert(type(newtankangle) == int)
        assert(type(newtankspeed) == int)
        assert(type(newtankposition[0]) == int)
        assert(type(newtankposition[1]) == int)
        assert(type(newturretangle) == int)

        return Command(angle=newtankangle, speed=newtankspeed, position=newtankposition,
                         turretangle=newturretangle, fire=fire, state=Command.State.operational)


class RemotePilot:
    """
    A "dummy' pilot which only executes the last instructions from a remote server.
    """

    def __init__(self):
        self.cmd = Command()
        self.cmd_exectured = False

    def update(self, tank, events, pressed, projectiles, walls):
        """
        Return latest instructions to the tank.
        """
        if self.cmd_executed:
            self.cmd.fire = False
        self.executed = True
        return self.cmd

    def remote_update(self, cmd):
        """
        Update the pilot with the information from the server.
        """
        self.cmd = cmd
        self.cmd_executed = False


class Client:
    """
    A TCP client to connect to the server and exchange tanks positions, angles, etc.
    """

    def __init__(self, ip, port, tanks):
        assert(len(tanks) == 1)
        self.remoteTanks = defaultdict(self.tank_factory)
        self.tanks = tanks
        self.ip = ip
        self.port = port
        self.data = b''
        self.socket = None
        self._previousMsg = defaultdict(lambda: None)

    def tank_factory(self):
        """
        Build a tank controled remotely.
        """
        return Tank(Config.tanks[0]["position"],
                    Config.tanks[0]["angle"],
                    (143, 138, 124, 255),
                    Turret(),
                    RemotePilot())

    def connect(self):
        """
        Connect the client to the server in non-blocking mode.
        """
        assert(len(self.tanks) == 1)
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
        tank = self.tanks[0]
        tank._id = cmd._id
        tank.position = Config.tanks[tank._id]["position"]
        tank.angle = Config.tanks[tank._id]["angle"]
        tank.turretangle = 0
        tank.color = Config.tanks[tank._id]["color"]

    def update(self):
        """
        Send the position of the local tanks to the server.
        Then, receive the position of the remote tanks from the server and update their pilots accordingly.
        """
        # Send positions of local tanks
        for tank in self.tanks:
            msg = Command().copy_from_tank(tank).encode()
            if self._previousMsg[tank._id] != msg:
                self._send_data(msg)
                self._previousMsg[tank._id] = msg
        # Read positions of remote self.tanks
        self._recv_data()
        while len(self.data) >= Command.Msglen:
            # Read a new command
            cmd = Command().decode(self.data[:Command.Msglen])
            self.data = self.data[Command.Msglen:]
            # Execute the command
            if cmd.state == Command.State.left:
                del(self.remoteTanks[cmd._id])
            else:
                tank = self.remoteTanks[cmd._id]
                if tank._id is None:
                    tank._id = cmd._id
                    tank.color = Config.tanks[tank._id]["color"]
                tank.pilot.remote_update(cmd)
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


def setBattleField(mode):
    """
    Prepare the tanks and walls of the battlefield.
    Parameter 'mode' can "local" or "server".
    """
    # Prepare tanks (2 if 'local' mode, 1 if 'server' mode) and client.
    if mode == "local":
        tanks = []
        for i in range(2):
            t = Tank(Config.tanks[i]["position"],
                     Config.tanks[i]["angle"],
                     Config.tanks[i]["color"],
                     Turret(),
                     Pilot(Config.keymap2players[i]))
            tanks.append(t)
        client = None
    elif mode == "server":
        tanks = []
        t = Tank(Config.tanks[0]["position"],
                 Config.tanks[0]["angle"],
                 Config.tanks[0]["color"],
                 Turret(),
                 Pilot(Config.keymap1player))
        tanks.append(t)
        client = Client(Config.ip, Config.port, tanks)
    else:
        raise RuntimeError("The mode '{}' doesn't exist.".format(mode))

    # Prepare walls
    walls = [Wall(w[0], w[1]) for w in Config.walls]

    return (tanks, walls, client)
