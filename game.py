#!/usr/bin/env python3


import sys
import pygame

from config import setBattleField, CONFIG


def main():

    # Init screen
    pygame.init()
    screen = pygame.display.set_mode(CONFIG["screen"])
    pygame.display.set_caption("Tank game")
    fpsClock = pygame.time.Clock()

    # Set up the battlefield
    (tanks, walls) = setBattleField()
    projectiles = []

    while True:

        # Process events
        events = pygame.event.get()
        for event in events:
            if ((event.type == pygame.QUIT)
                or (event.type == pygame.KEYUP and event.key == pygame.K_ESCAPE)):
                print("Bye!")
                pygame.quit()
                sys.exit()

        # Process pushed keys
        pressed = pygame.key.get_pressed()

        # Compute new positions
        for tank in tanks:
            tank.update(events, pressed, projectiles, walls)
        for projectile in projectiles:
            projectile.update(walls, tanks)

        # Redraw boards
        screen.fill((220, 220, 220, 0))
        for wall in walls:
            wall.draw(screen)
        for tank in tanks:
            tank.draw(screen)
        for projectile in projectiles:
            projectile.draw(screen)

        # Remove projectiles which have left the screen
        for i in range(len(projectiles)-1, -1, -1):
            projX, projY = projectiles[i].position
            if not ((0 <= projX <= CONFIG["screen"][0]) and (0 <= projY <= CONFIG["screen"][1])):
                del(projectiles[i])

        # Update the display
        pygame.display.update()

        # Ensure constant FPS
        fpsClock.tick(CONFIG["fps"])


if __name__ == '__main__':
    main()
