#!/usr/bin/env python3


import sys
import pygame

from config import Config
from resources import Tank, Turret, Pilot, Wall, Client


def main():

    mode = "server" # Possible modes are "server" and "local"

    # Init screen
    pygame.init()
    screen = pygame.display.set_mode(Config.screen)
    pygame.display.set_caption("Tank game")
    fpsClock = pygame.time.Clock()

    # prepare the battlefield
    tanks, walls = setBattleField(mode)
    projectiles = []

    # Connect to the server
    client = None
    if mode == "server":
        client = Client(Config.ip, Config.port, tanks)
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

        # Get remote tanks from server
        remoteTanks = []
        if client:
            remoteTanks = client.update()

        # Compute new positions
        for obj in tanks + remoteTanks + projectiles:
            obj.update(events, pressed, projectiles, walls, tanks)

        # Remove projectiles which have left the screen
        maxX, maxY = Config.screen
        for i in range(len(projectiles)-1, -1, -1):
            projX, projY = projectiles[i].position
            if not ((0 <= projX <= maxX) and (0 <= projY <= maxY)):
                del(projectiles[i])

        # Redraw boards
        screen.fill((220, 220, 220, 0))
        for obj in walls + tanks + remoteTanks + projectiles:
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
