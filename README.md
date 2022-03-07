# Python Voice Chat

## Setup

### Windows

#### Dependancy Installation:

- ``pip install -r requirements.txt``

You might have to install `pipwin` (`pip install pipwin`) and install the packages
using ``pipwin install -r requirements.txt``

### Linux

#### Dependancy Installation:

- ``sudo apt install -y portaudio19-dev``
- ``sudo apt install -y pyaudio``
- ``pip install -r requirements.txt``

## Usage

### Server

- Run ``server.py`` to start the server. You will be prompted for the port on 
  which the server will be listening for connections.
- If you intend to use this program across the internet, ensure you have port forwarding that is forwarding the port the server is running on to the server's machine local IP (the IP displayed on the server program) and the correct port.

### Client

- Clients can connect across the internet by entering your public IP (as long as you have port forwarding to your machine) and the port the machine is running on or in the same network by entering the IP displayed on the server.
- After connecting to the server you will be prompted to enter your username and the id of a room
  you want to connect to. After that you will be able to communicate with the people in this room.

#### Commands

After connecting to the room you can use these commands to control your voice transmission:

- `start`: start talking. After this command the sound from your mic will be sent to the server.
- `stop`: stop talking. After this command no sound will be captured.
- `disconnect`: disconnect from the server.


## Requirements

- Python 3
- PyAudio
- Socket Module (standard library)
- Threading Module (standard library)

# Reference

Based on [TomPrograms](https://github.com/TomPrograms) [Python-Voice-Chat](https://github.com/TomPrograms/Python-Voice-Chat) project.

## License
[MIT](https://choosealicense.com/licenses/mit/)
