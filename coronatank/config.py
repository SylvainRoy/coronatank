#!/usr/bin/env python3

"""
This file contains the configuration of the game.
"""


import pygame


class Config:

    fps = 50
    screen = (800, 600)

    maxInt = 99999999

    tankDimensions = (50, 40)
    tankMaxSpeed = 6
    tankDeltaAngle = 6
    tankDeathDuration = 5

    turretColor = (50, 50, 50, 255)
    turretDeltaAngle = 2

    wallColor = (200, 120, 10)
    wallThickness = 10

    # Negative coordinates are measured backward from the bottom/right
    tanks = [
        {"position": (50, 50), "angle": -45, "color": (20, 150, 50, 255)},
        {"position": (-50, -50), "angle": 135, "color": (50, 150, 250, 255)},
        {"position": (-50, 50), "angle": -135, "color": (150, 20, 50, 255)},
        {"position": (50, -50), "angle": 45, "color": (150, 50, 20, 255)}
    ]

    # Walls can only be vertical or horizontal.
    # The first coordindate MUST be at the top-left.
    walls = [
        ((200, 100), (200, 450)),
        ((200, 300), (500, 300)),
        ((450, 450), (650, 450)),
        ((650, 200), (650, 450)),
        ((400, 200), (650, 200))
    ]

    # One player using the keyboard
    keymap1player = {"forward":     pygame.K_w,
                     "backward":    pygame.K_s,
                     "left":        pygame.K_a,
                     "right":       pygame.K_d,
                     "turretRight": pygame.K_RIGHT,
                     "turretLeft":  pygame.K_LEFT,
                     "fire":        pygame.K_UP}

    # Two players sharing the keyboard
    keymap2players = [{"forward":     pygame.K_w,
                       "backward":    pygame.K_s,
                       "left":        pygame.K_a,
                       "right":       pygame.K_d,
                       "turretRight": pygame.K_b,
                       "turretLeft":  pygame.K_c,
                       "fire":        pygame.K_v},
                      {"forward":     pygame.K_UP,
                       "backward":    pygame.K_DOWN,
                       "left":        pygame.K_LEFT,
                       "right":       pygame.K_RIGHT,
                       "turretRight": pygame.K_SLASH,
                       "turretLeft":  pygame.K_COMMA,
                       "fire":        pygame.K_PERIOD}]
