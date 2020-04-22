#!/usr/bin/env python3

"""
The main file of the game.
Usage:

    python3 game.py
or
    python3 game.py --server <ip:port>
"""

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import sys
import pygame
import argparse

from . import Config
from . import Tank, Turret, Pilot, Wall
from . import Client


def main():

    # Parsing command line
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", help="IP:port of the server")
    args = parser.parse_args()
    mode = "local"
    if args.server:
        ip, port = args.server.split(":")
        port = int(port)
        mode = "server"

    # Init screen
    pygame.init()
    screen = pygame.display.set_mode(Config.screen)
    pygame.display.set_caption("Tank game")
    fpsClock = pygame.time.Clock()

    # prepare the battlefield
    tanks, walls = setBattleField(mode)
    projectiles = {}

    # Connect to the server
    client = None
    if mode == "server":
        client = Client(ip, port, tanks)
        client.connect()

    while True:

        # Collect events and pressed keys
        events = pygame.event.get()
        pressed = pygame.key.get_pressed()

        # Quit?
        for event in events:
            if ((event.type == pygame.QUIT)
                or (event.type == pygame.KEYUP and event.key == pygame.K_ESCAPE)):
                print("Bye!")
                pygame.quit()
                sys.exit()

        # Synchronize with server
        remoteTanks = []
        if client:
            remoteTanks = client.synchronize()

        # Compute new positions
        for obj in tanks + remoteTanks + list(projectiles.values()):
            obj.update(events, pressed, projectiles, walls, tanks, client)

        # Remove projectiles which have left the screen
        maxX, maxY = Config.screen
        for projectile in list(projectiles.values()):
            projX, projY = projectile.position
            if not ((0 <= projX <= maxX) and (0 <= projY <= maxY)):
                del(projectiles[projectile._id])

        # Redraw boards
        screen.fill((220, 220, 220, 0))
        for obj in walls + tanks + remoteTanks + list(projectiles.values()):
            obj.draw(screen)
        pygame.display.update()

        # Ensure constant FPS
        fpsClock.tick(Config.fps)


def setBattleField(mode):
    """
    Prepare the tanks and walls of the battlefield.
    Parameter 'mode' can be "local" or "server".
    """
    # Prepare tanks (2 if 'local' mode, 1 if 'server' mode) and client.
    tanks = []
    if mode == "local":
        for i in range(2):
            t = Tank(Config.tanks[i]["position"],
                     Config.tanks[i]["angle"],
                     Config.tanks[i]["color"],
                     Turret(),
                     Pilot(Config.keymap2players[i]))
            tanks.append(t)
    elif mode == "server":
        t = Tank(Config.tanks[0]["position"],
                 Config.tanks[0]["angle"],
                 Config.tanks[0]["color"],
                 Turret(),
                 Pilot(Config.keymap1player))
        tanks.append(t)
    else:
        raise RuntimeError("The mode '{}' doesn't exist.".format(mode))
    # Prepare walls
    walls = [Wall(w[0], w[1]) for w in Config.walls]
    return (tanks, walls)


if __name__ == '__main__':
    main()
