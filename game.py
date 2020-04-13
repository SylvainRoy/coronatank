#!/usr/bin/env python3


import sys
import pygame

from config import CONFIG
from resources import setBattleField


def main():

    # Init screen
    pygame.init()
    screen = pygame.display.set_mode(CONFIG["screen"])
    pygame.display.set_caption("Tank game")
    fpsClock = pygame.time.Clock()

    # Set up the battlefield
    (tanks, walls, client) = setBattleField("local")
    projectiles = []

    # Connect to server
    if client:
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
        maxX, maxY = CONFIG["screen"]
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
        fpsClock.tick(CONFIG["fps"])


if __name__ == '__main__':
    main()
