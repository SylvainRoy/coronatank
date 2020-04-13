#!/usr/bin/env python3


import pygame
import socket
import time

from collections import defaultdict
from math import cos, sin, sqrt, radians, copysign
from enum import Enum

from tools import encode_message, decode_message, MSGLEN
from config import CONFIG


class Tank:
    """
    A vehicule which can move, fire, collide with walls.
    It requires a turret and a pilot.
    """

    def __init__(self, dimensions, position, maxSpeed, angle, deltaAngle, color, wallThickness, turret, pilot):
        self.dimensions = dimensions
        self.position = (position[j] % CONFIG["screen"][j] for j in range(2))
        self.maxSpeed = maxSpeed
        self.angle = angle
        self.deltaAngle = deltaAngle
        self.color = color
        self.speed = 0
        self.wallThickness = wallThickness
        self.turret = turret
        self.turret.tank = self
        self.pilot = pilot
        self.destroyed = False
        self._id = None
        self.fire = False

    def draw(self, screen):
        """
        Draws the tank.
        """
        surface = pygame.Surface(self.dimensions).convert_alpha()
        surface.fill((0,0,0,0))
        # Draw the body of the tank
        pygame.draw.rect(surface, self.color, pygame.Rect((0,0), self.dimensions))
        # Draw the caterpillars
        pygame.draw.rect(surface, (255,255,255,255),
                         pygame.Rect((0,0),
                                     (self.dimensions[0], self.dimensions[1]//6)))
        pygame.draw.rect(surface, (255,255,255,255),
                         pygame.Rect((0, 5*self.dimensions[1]//6 + 1),
                                     self.dimensions))
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
        if self.destroyed:
            return
        # Get instruction from pilot
        commands = self.pilot.update(self, events, pressed, projectiles, walls)
        # Update the tank accordingly
        self.angle, self.speed, self.position, self.turret.angle, self.fire = commands
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
        innersize = min(self.dimensions) - 2 * self.wallThickness
        return pygame.Rect((position[0] - innersize//2, position[1] - innersize//2),
                           (innersize, innersize))

    def get_avg_rect(self, position=None):
        """
        Returns a rectangle of the tank to use for projectile collision detection.
        """
        if position is None:
            position = self.position
        avgsize = (self.dimensions[0] + self.dimensions[1]) // 2
        return pygame.Rect((position[0] - avgsize//2, position[1] - avgsize//2),
                           (avgsize, avgsize))

    def destroy(self):
        """
        Destroys the tank.
        """
        self.speed = 0
        self.color = (30, 30, 30)
        self.destroyed = True


class Turret:
    """
    The turrets that seats on top of the tanks.
    """

    def __init__(self, dimensions, deltaAngle, maxAngularSpeed, color):
        self.angle = 0
        self.deltaAngle = deltaAngle
        self.maxAngularSpeed = maxAngularSpeed
        self.dimensions = dimensions
        self.color = color
        self.tank = None

        self.angularSpeed = 0
        self.centerX = self.dimensions[0] // 2
        self.centerY = self.dimensions[1] // 2
        self.canonLen = min(self.dimensions) // 2
        self.radius = self.canonLen // 2

    def draw(self, surface):
        """
        Draws the tank.
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
        aX = int(self.tank.position[0] + self.tank.dimensions[0] * 0.6 * cos(radians(angle)))
        aY = int(self.tank.position[1] - self.tank.dimensions[1] * 0.6 * sin(radians(angle)))
        projectiles.append(Amunition((aX, aY), angle))


AmunitionState = Enum('AmunitionState', 'active detonated destroyed')


class Amunition:
    """
    The projectiles fired by the tank.
    """

    def __init__(self, position, angle):
        self.position = position
        self.angle = angle
        self.speed = 10
        self.state = AmunitionState.active

    def draw(self, screen):
        """
        Draws the projectile.
        """
        if self.state == AmunitionState.active:
            pygame.draw.circle(screen, (0,0,0,255), self.position, 3)
        elif self.state == AmunitionState.detonated:
            pygame.draw.circle(screen, (0,0,0,255), self.position, 30)

    def update(self, events, pressed, projectiles, walls, tanks):
        """
        Updates the state of the projectile.
        """
        if self.state == AmunitionState.detonated:
            self.destroy()
            return
        # Update position
        dx = int(self.speed * cos(radians(self.angle)))
        dy = int(self.speed * -sin(radians(self.angle)))
        x, y = self.position
        self.position = (x + dx, y + dy)
        # Detect collision with a wall
        for wall in walls:
            if wall.rect.collidepoint(self.position):
                self.state = AmunitionState.detonated
        # Detect collision with a tank
        for tank in tanks:
            if tank.get_avg_rect().collidepoint(self.position):
                self.state = AmunitionState.detonated
                tank.destroy()

    def destroy(self):
        """
        Destroys the projectile.
        """
        # Move projectile out of the screen for automatic clean up.
        self.state = AmunitionState.destroyed
        self.position = (-10, -10)
        self.angle = 180
        self.speed = 10


class Wall:
    """
    The walls of the battlefield.
    """

    def __init__(self, beg, end, thickness, color):
        assert(beg[0] <= end[0])
        assert(beg[1] <= end[1])
        self.beg = beg
        self.end = end
        self.thickness = thickness
        self.color = color
        self.rect = pygame.Rect((beg[0]-thickness, beg[1]-thickness),
                                (end[0]-beg[0]+2*thickness, end[1]-beg[1]+2*thickness))

    def draw(self, screen):
        """
        Draws the wall.
        """
        pygame.draw.line(screen, self.color, self.beg, self.end, 4)

    def draw_rect(self, screen):
        """
        Draws the rectangle used for collision detection.
        """
        pygame.draw.rect(screen, (0,0,0), self.rect, 1)


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

        # Compute new tank angle based on player's input
        rotation = tank.deltaAngle * (pressed[self.left] - pressed[self.right])
        newtankangle = tank.angle + rotation

        # Update tank speed based on player's input
        translation = pressed[self.forward] - pressed[self.backward]
        if translation != 0:
            newtankspeed = max(-tank.maxSpeed, min(tank.maxSpeed, tank.speed + translation))
        elif tank.speed != 0:
            # Progressively stop the tank if no input from the player
            newtankspeed = copysign(abs(tank.speed)-1, tank.speed)
        else:
            newtankspeed = 0

        # Compute move considering possible collision
        delta = newtankspeed
        direction = copysign(1, delta)
        while True:
            # Compute tentative position
            dx = delta * cos(radians(newtankangle))
            dy = delta * -sin(radians(newtankangle))
            x, y = tank.position
            newtankposition = (x + dx, y + dy)
            # Reduce move in case of collision
            if tank.detect_collision(newtankposition, walls):
                delta -= direction
                newtankspeed = 0
            else:
                break

        # Compute turret angular speed
        rotation = tank.turret.deltaAngle * (pressed[self.turretLeft] - pressed[self.turretRight])
        if rotation != 0:
            tank.turret.angularSpeed = max(-tank.turret.maxAngularSpeed,
                                           min(tank.turret.maxAngularSpeed,
                                               tank.turret.angularSpeed + rotation))
        elif tank.turret.angularSpeed != 0:
            # Progressively stop the turret if no input from player
            tank.turret.angularSpeed = copysign(abs(tank.turret.angularSpeed)-1,
                                                tank.turret.angularSpeed)
        # new turret angle
        newturretangle = tank.turret.angle + tank.turret.angularSpeed

        # Fire a new projectile
        fire = False
        if any((e.type == pygame.KEYUP and e.key == self.fire for e in events)):
            fire = True

        return newtankangle, newtankspeed, newtankposition, newturretangle, fire


class RemotePilot:
    """
    A "dummy' pilot which only executes instructions from a server.
    """

    def __init__(self):
        self.position = (0,0)
        self.angle = 0

    def update(self, tank, events, pressed, projectiles, walls):
        """
        Return latest instructions to the tank.
        """
        fire = self.fire
        self.fire = False
        return self.angle, 0, self.position, self.angleturret, fire

    def remote_update(self, position, angle, angleturret, fire):
        """
        Update the pilot with the information from the server.
        """
        self.position = position
        self.angle = angle
        self.angleturret = angleturret
        self.fire = fire


class Client:
    """
    A TCP client to connect to the server and exchange tanks positions, angles, etc.
    """

    def __init__(self, ip, port, tanks, remote_tank_factory):
        assert(len(tanks) == 1)
        self.remoteTanks = defaultdict(remote_tank_factory)
        self.tanks = tanks
        self.ip = ip
        self.port = port
        self.data = b''
        self.socket = None
        self._previousMsg = defaultdict(lambda: None)

    def connect(self):
        """
        Connect the client to the server in non-blocking mode.
        """
        assert(len(self.tanks) == 1)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        err = self.socket.connect(('127.0.0.1', 8888))
        self.socket.setblocking(0)
        data = b''
        while len(data) < MSGLEN:
            try:
                r = self.socket.recv(MSGLEN)
                if r == b'':
                    raise RuntimeError("Connection with server broken.")
            except BlockingIOError:
                r = b''
            data += r
        (_id, x, y, angle, _, _) = decode_message(data)
        x = x % CONFIG["screen"][0]
        y = y % CONFIG["screen"][1]
        self.tanks[0]._id = _id
        self.tanks[0].position = (x,y)
        self.tanks[0].angle = angle

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

    def _recv_data(self):
        """
        Internal method to recv data from the server.
        """
        try:
            data = self.socket.recv(MSGLEN)
            if data == b'':
                raise RuntimeError("Connection with server broken.")
        except BlockingIOError:
            data = b''
        self.data += data

    def update(self):
        """
        Send the position of the local tanks to the server.
        Then, receive the position of the remote tanks from the server and update their pilots accordingly.
        """
        # Send positions of local tanks
        for tank in self.tanks:
            msg = encode_message(tank._id, int(tank.position[0]), int(tank.position[1]),
                                 int(tank.angle), int(tank.turret.angle), tank.fire)
            if self._previousMsg[tank._id] != msg:
                self._send_data(msg)
                self._previousMsg[tank._id] = msg
        # Read positions of remote self.tanks
        self._recv_data()
        while len(self.data) >= MSGLEN:
            _id, x, y, angle, angleturret, fire = decode_message(self.data[:MSGLEN])
            x = x % CONFIG["screen"][0]
            y = y % CONFIG["screen"][1]
            self.data = self.data[MSGLEN:]
            t = self.remoteTanks[_id].pilot.remote_update((x,y), angle, angleturret, fire)
        return list(self.remoteTanks.values())


def setBattleField(mode):
    """
    Prepare the tanks and walls of the battlefield.
    Parameter 'mode' can "local" or "server".
    """

    # Prepare tanks (2 if 'local', 1 if 'server') and client.
    if mode == "local":
        tanks = []
        for i in range(2):
            x, y = (CONFIG["tanks"][i]["position"][j] % CONFIG["screen"][j] for j in range(2))
            t = Tank(CONFIG["tankDimensions"],
                     (x, y),
                     CONFIG["tankMaxSpeed"],
                     CONFIG["tanks"][i]["angle"],
                     CONFIG["tankDeltaAngle"],
                     CONFIG["tanks"][i]["color"],
                     CONFIG["wallThickness"],
                     Turret(CONFIG["tankDimensions"],
                            CONFIG["turretDeltaAngle"],
                            CONFIG["turretMaxAngularSpeed"],
                            CONFIG["turretColor"]),
                     Pilot(CONFIG["keymap2players"][i]))
            tanks.append(t)
        client = None

    elif mode == "server":
        tanks = []
        x, y = (CONFIG["tanks"][0]["position"][j] % CONFIG["screen"][j] for j in range(2))
        t = Tank(CONFIG["tankDimensions"],
                 (x, y),
                 CONFIG["tankMaxSpeed"],
                 CONFIG["tanks"][0]["angle"],
                 CONFIG["tankDeltaAngle"],
                 CONFIG["tanks"][0]["color"],
                 CONFIG["wallThickness"],
                 Turret(CONFIG["tankDimensions"],
                        CONFIG["turretDeltaAngle"],
                        CONFIG["turretMaxAngularSpeed"],
                        CONFIG["turretColor"]),
                 Pilot(CONFIG["keymap1player"]))
        tanks.append(t)
        client = Client(CONFIG["ip"], CONFIG["port"], tanks, remote_tank_factory)

    else:
        raise RuntimeError("The mode '{}' doesn't exist.".format(mode))

    # Prepare walls
    walls = [Wall((200, 100), (200, 450), CONFIG["wallThickness"], CONFIG["wallColor"]),
             Wall((200, 300), (500, 300), CONFIG["wallThickness"], CONFIG["wallColor"]),
             Wall((450, 450), (650, 450), CONFIG["wallThickness"], CONFIG["wallColor"]),
             Wall((650, 200), (650, 450), CONFIG["wallThickness"], CONFIG["wallColor"]),
             Wall((400, 200), (650, 200), CONFIG["wallThickness"], CONFIG["wallColor"])]

    return (tanks, walls, client)


def remote_tank_factory():
    """
    Build a tank controled remotely.
    """
    x, y = (100, 100)
    t = Tank(CONFIG["tankDimensions"],
             (x, y),
             CONFIG["tankMaxSpeed"],
             CONFIG["tanks"][0]["angle"],
             CONFIG["tankDeltaAngle"],
             (143, 138, 124, 255),
             CONFIG["wallThickness"],
             Turret(CONFIG["tankDimensions"],
                    CONFIG["turretDeltaAngle"],
                    CONFIG["turretMaxAngularSpeed"],
                    CONFIG["turretColor"]),
             RemotePilot())
    return t
