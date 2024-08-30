# Rally Robopilot Project

This repository holds a sandbox driving simulation controllable via a network interface. 


# ToDo & Done

* Streamline single track loading
  * **ToDo -** automated loading meshes (track, bounds, decorations)
  * **ToDo -** car start positioning
* Target track modeling
  * **ToDo -** road mesh
  * **ToDo -** decorations
* Sensing
  * **Done -** raycasting aligned with speed vector (not with car)
  * **ToDo -** define recasting parameters 
    * number of rays
    * field of scanning
* Car physic
  * **ToDo -** Make over for less soapy control
* Interface
  * **Done -** Socket & communication protocol
  * **Done -** in-control streaming
    * **ToDo -** Polish communication protocol
    * **ToDo -** Decide to add time dilation ? (Running simulation faster) or let student figure it ?
  * **Done -** out sensing streaming
    * **Done -** sensing parameters (frequency, resolution, etc)
    * **Done -** position/orientation/velocity
    * **Done -** raycasting
    * **Done -** image
* Dockerization
  * **ToDo -** test dockerization 

# Installation

```
pip install -r requirements.txt
```

The following requirement is optional and only needed to run the examplar data_collector.py
```
imageio==2.35.1
```

To run the game
```
python main.py
```

# Generality
Launching main.py starts a race with a single car on the provided track. 
This track can be controlled either by keyboard (*AWSD*) or by a socket interface. 
An example of such interface is included in the code in *example_data_collector.py*.

# Communication protocol

A remote controller can be impemented using TCP socket connecting on localhost on port 7654. 
Different commands can be issued to the race simulation to control the car.

The car simulator expect specific commands to be sent. A command is a specific set of words or numbers. 
**Spaces** are used as elements separator in a single command. **Semi-colon (;)** as command separator.

##  Car controls
```
push|release forward|right|left|back;
```
To simulate key press and control the car.

## Reset controls
```
set position x,y,z;
```
To set the reset position at the (x,y,z) location. x,y,z are float numbers with english style dot separator (e,g. 3.1415, 2.5, 6.34234) themselves separated by a comma.
```
set rotation a;
```
to set the car orientation, with a being a float number in degrees
```
set speed v;
```
to set the starting speed after reset

```
reset;
```
to reset the car at the provided location.

## Ray sensing

```
set ray visible|hidden;
```
To toggle the ray sensor visibility. In direct play **v** can be used to toggle ray visibility

# Multiplayer

To run multiplayer, run the `main.py` file and click `Multiplayer`. Then enter the ip address (this can be defaulted to 'localhost') and the port (default: 25565). Click `Create - Server` and then click `Join - Server`.
For others to join, run the `main.py`, click `Multiplayer` and then click `Join Server`. Enter the public ip address and the port of the server. Click `JOIN` and then you're in. Unlimited people can join!

If you don't want to play on a server, run the `main.py` file and click `Singleplayer`.

# Controls

W - Drive
S - Brake
A, D - Turn
SPACE - Hand Brake
ESCAPE - Pause Menu
G - Respawn

# Credits
This code is based on the repository [https://github.com/mandaw2014/Rally](https://github.com/mandaw2014/Rally)
