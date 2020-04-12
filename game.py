#!/usr/bin/env python3


import sys
import pygame
from dataclasses import dataclass, field
from math import cos, sin, radians

from resources import Tank, Turret, Amunition, Wall, Pilot


@dataclass
class Configuration:

    fps = 50
    screen = (800, 600)

    tankDimensions = (50, 40)
    tankPosition1 = (50, 50)
    tankPosition2 = (750, 550)
    tankMaxSpeed = 5 # 7
    tankAngle1 = 0
    tankAngle2 = 180
    tankDeltaAngle = 6
    tankColor1 = (20, 150, 50, 255)
    tankColor2 = (50, 150, 250, 255)

    turretColor = (50, 50, 50, 255)
    turretDeltaAngle = 3
    turretMaxAngularSpeed = 5 # 7

    wallColor = (200, 120, 10)
    wallThickness = 10

    # One player on the keyboard
    keymap1 = {"forward": pygame.K_w,
               "backward": pygame.K_s,
               "left": pygame.K_a,
               "right": pygame.K_d,
               "turretRight": pygame.K_RIGHT,
               "turretLeft": pygame.K_LEFT,
               "fire": pygame.K_UP}

    # Two players sharing the keyboard
    keymap2 = {"forward": pygame.K_w,
               "backward": pygame.K_s,
               "left": pygame.K_a,
               "right": pygame.K_d,
               "turretRight": pygame.K_b,
               "turretLeft": pygame.K_c,
               "fire": pygame.K_v}
    keymap3 = {"forward": pygame.K_UP,
               "backward": pygame.K_DOWN,
               "left": pygame.K_LEFT,
               "right": pygame.K_RIGHT,
               "turretRight": pygame.K_SLASH,
               "turretLeft": pygame.K_COMMA,
               "fire": pygame.K_PERIOD}

Config = Configuration()


def main():

    # Init screen
    pygame.init()
    screen = pygame.display.set_mode(Config.screen)
    pygame.display.set_caption("Tank game")
    fpsClock = pygame.time.Clock()

    tanks = [Tank(Config.tankDimensions,
                  Config.tankPosition1,
                  Config.tankMaxSpeed,
                  Config.tankAngle1,
                  Config.tankDeltaAngle,
                  Config.tankColor1,
                  Config.wallThickness,
                  Turret(Config.tankDimensions,
                         Config.turretDeltaAngle,
                         Config.turretMaxAngularSpeed,
                         Config.turretColor),
                  Pilot(Config.keymap2)),
             Tank(Config.tankDimensions,
                  Config.tankPosition2,
                  Config.tankMaxSpeed,
                  Config.tankAngle2,
                  Config.tankDeltaAngle,
                  Config.tankColor2,
                  Config.wallThickness,
                  Turret(Config.tankDimensions,
                         Config.turretDeltaAngle,
                         Config.turretMaxAngularSpeed,
                         Config.turretColor),
                  Pilot(Config.keymap3))]

    projectiles = []
    walls = [Wall((200, 100), (200, 450), Config.wallThickness, Config.wallColor),
             Wall((200, 300), (500, 300), Config.wallThickness, Config.wallColor),
             Wall((450, 450), (650, 450), Config.wallThickness, Config.wallColor),
             Wall((650, 200), (650, 450), Config.wallThickness, Config.wallColor),
             Wall((400, 200), (650, 200), Config.wallThickness, Config.wallColor)]

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
            #wall.draw_rect(screen)
        for tank in tanks:
            tank.draw(screen)
        for projectile in projectiles:
            projectile.draw(screen)

        # Remove projectiles which have left the screen
        for i in range(len(projectiles)-1, -1, -1):
            projX, projY = projectiles[i].position
            if not ((0 <= projX <= Config.screen[0]) and (0 <= projY <= Config.screen[1])):
                del(projectiles[i])

        # Update the display
        pygame.display.update()

        # Ensure constant FPS
        fpsClock.tick(Config.fps)


if __name__ == '__main__':
    main()
