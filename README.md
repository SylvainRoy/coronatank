# Description

A two player tank game based on python3 / pygame.
Or... Me playing with pygame while locked at home because of the coronavirus. :-)

It can be played by two player on a single computer.
It can also be played by up to four players, each of them on its own machine. (You'll need to run a server, see below.)


# How to install it?

Ensure to have python (3.6 or above) and then install pygame:

    python -m pip install pygame

Then, to launch the game:

    python -m coronatank.game

Press all the keys of your keyboard to figure out how to move, rotate,
rotate the turret, fire with the two tanks. (Enjoy!)


# How to run it in server mode?

The first thing to do is to run the server:

    python -m coronatank.server --listen <ip:port>

Then, each player can run the client:

    python -m coronatank.game --server <ip:port>


# How to build/use the docker image of the server?

The docker image is automatically built on docker hub. So, the simplest option is to pull it from there:

    docker run -p 8888:8888 -d sroy/coronatank

In case you want to build it yourself:

    docker build -t <user/repository> .
    docker run -p 8888:8888 -d <user/repository>

You might want the server to run in the cloud to play with friends all over the world.
Here are the commands to do just that with Azure:

    az group create --name tank-group --location westeurope
    DNS_NAME_LABEL=tank-sroy-$RANDOM
    az container create --resource-group tank-group --name tank-container --image sroy/tank:latest --ports 8888 --dns-name-label $DNS_NAME_LABEL --location westeurope

Then, to check its state:

    az container show --resource-group tank-group --name tank-container --query containers[0].instanceView.currentState.state

To see the logs:

    az container logs --resource-group tank-group --name tank-container

And to start/stop it:

    az container start --resource-group tank-group --name tank-container
    az container stop --resource-group tank-group --name tank-container



# What's next?

 * A small AI to allow a single player mode.
 * Better weapons!
 * Sprites!
 * Sounds!

No commitment here. This is a toy project whose sole purpose is to be fun (for the developer!).
