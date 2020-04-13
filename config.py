#!/usr/bin/env python3

"""
This file contains the configuration of the game.
"""


import pygame
from resources import Tank, Turret, Wall, Pilot

CONFIG = {
    "fps": 50,
    "screen": (800, 600),

    "tankDimensions": (50, 40),
    "tankMaxSpeed": 5, # 7
    "tankDeltaAngle": 6,

    "turretColor": (50, 50, 50, 255),
    "turretDeltaAngle": 3,
    "turretMaxAngularSpeed": 5, # 7

    "wallColor": (200, 120, 10),
    "wallThickness": 10,

    "tanks": [
        {"position": (50, 50), "angle": -45, "color": (20, 150, 50, 255)},
        {"position": (750, 550), "angle": 135, "color": (50, 150, 250, 255)}
    ],

    # One player on the keyboard
    "keymap1player": {"forward":     pygame.K_w,
                      "backward":    pygame.K_s,
                      "left":        pygame.K_a,
                      "right":       pygame.K_d,
                      "turretRight": pygame.K_RIGHT,
                      "turretLeft":  pygame.K_LEFT,
                      "fire":        pygame.K_UP},

    # Two players sharing the keyboard
    "keymap2players": [{"forward":     pygame.K_w,
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
}


def setBattleField():
    """
    Prepare the tanks and walls of the battlefield.
    """

    # Prepare two tanks
    tanks = []
    for i in range(2):
        t = Tank(CONFIG["tankDimensions"],
                 CONFIG["tanks"][i]["position"],
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

    # Prepare walls
    walls = [Wall((200, 100), (200, 450), CONFIG["wallThickness"], CONFIG["wallColor"]),
             Wall((200, 300), (500, 300), CONFIG["wallThickness"], CONFIG["wallColor"]),
             Wall((450, 450), (650, 450), CONFIG["wallThickness"], CONFIG["wallColor"]),
             Wall((650, 200), (650, 450), CONFIG["wallThickness"], CONFIG["wallColor"]),
             Wall((400, 200), (650, 200), CONFIG["wallThickness"], CONFIG["wallColor"])]

    return (tanks, walls)
