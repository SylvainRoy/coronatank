# Description

A two player tank game based on python3 / pygame.
Or... Me playing with pygame while locked at home because of the coronavirus. :-)

It can be played by two player on a single computer.
It can also be played by up to four players, each of them on its own machine. (You'll need to run a server, see below.)


# How to install it?

Ensure to have python (3.6 or above) and then install pygame:

    python3 -m pip install pygame

Then, to launch the game:

    python3 game.py

Press all the keys of your keyboard to figure out how to move, rotate,
rotate the turret, fire with the two tanks. (Enjoy!)


# How to run it in server mode?

The first thing to do is to run the server:

    python3 server.py --listen <ip:port>

Then, each player can run the client:

    python3 game.py --server <ip:port>


# What's next?

 * A docker image of the server to easily deploy it in the cloud.
 * A small AI to allow a single player mode.
 * Better weapons!
 * Sprites!
 * Sounds!

No commitment here. This is a toy project whose sole purpose is to be fun (for the developer!).
