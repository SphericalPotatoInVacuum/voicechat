#!/usr/bin/python3

import json
import socket
import threading

import pyaudio
from loguru import logger

from protocol import Message, MessageType

CHUNK_SIZE = 512
AUDIO_FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100


class Client:
    def __init__(self):
        self.lock = threading.Lock()
        self.talking = False

        # initialise microphone recording
        self.p = pyaudio.PyAudio()

        # select input device
        while True:
            try:
                for i in range(self.p.get_device_count()):
                    device = self.p.get_device_info_by_index(i)
                    if device['maxInputChannels'] == 0:
                        continue
                    print(f'{device["index"]}: {device["name"]}, {device["defaultSampleRate"]}HZ')
                input_device_index = int(input('Select input device index: '))

                self.recording_stream = self.p.open(
                    format=AUDIO_FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    input_device_index=input_device_index,
                    frames_per_buffer=CHUNK_SIZE * 3)

                break
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(e)

        # select output device
        while True:
            try:
                for i in range(self.p.get_device_count()):
                    device = self.p.get_device_info_by_index(i)
                    if device['maxOutputChannels'] == 0:
                        continue
                    print(f'{device["index"]}: {device["name"]}, {device["defaultSampleRate"]}HZ')
                output_device_index = int(input('Select output device index: '))

                self.playing_stream = self.p.open(
                    format=AUDIO_FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    output=True,
                    output_device_index=output_device_index,
                    frames_per_buffer=CHUNK_SIZE * 3)

                break
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(e)

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        while True:
            try:
                self.target_ip = input('Enter IP address of server --> ')
                self.target_port = int(input('Enter target port of server --> '))

                self.s.connect((self.target_ip, self.target_port))

                break
            except KeyboardInterrupt:
                raise
            except BaseException as e:
                logger.error(e)

        print('Connected to Server!')

        while True:
            username = input('Enter username: ')
            room_id = input('Enter room id: ')
            Message.build_message(MessageType.CONNECTION_REQUEST, json.dumps({
                'username': username,
                'room_id': room_id
            })).send(self.s)

            m = Message.read_message(self.s)
            assert m.message_type == MessageType.CONNECTION_RESPONSE
            d = json.loads(m.content)
            if d['result'] == 'ok':
                break
            print(f'Could not connect to room: {d["reason"]}')

        # start threads
        receive_thread = threading.Thread(target=self.receive_server_data).start()
        send_thread = threading.Thread(target=self.send_data_to_server).start()

        while True:
            command = input()
            if command == 'start':
                self.talking = True
                with self.lock:
                    Message.build_message(MessageType.START_TALKING, 'empty_content').send(self.s)
            elif command == 'stop':
                self.talking = False
                with self.lock:
                    Message.build_message(MessageType.STOP_TALKING, 'empty_content').send(self.s)
            elif command == 'disconnect':
                with self.lock:
                    Message.build_message(MessageType.DISCONNECT, 'empty_content').send(self.s)
                    self.s.close()
                    exit(0)
            else:
                print(f'No such command: {command}')

    def receive_server_data(self):
        while True:
            try:
                m = Message.read_message(self.s)
                if m.message_type is MessageType.VOICE_DATA:
                    self.playing_stream.write(m.content)
                elif m.message_type is MessageType.ROOM_STATE:
                    room = json.loads(m.content)
                    s = []
                    for client, talking in room.items():
                        if talking:
                            s.append(f'({client})')
                        else:
                            s.append(client)
                    print(f'{" ".join(s)}')
            except KeyboardInterrupt:
                raise
            except BaseException as e:
                logger.error(e)

    def send_data_to_server(self):
        while True:
            try:
                if self.talking:
                    data = self.recording_stream.read(CHUNK_SIZE, False)
                    with self.lock:
                        Message.build_message(MessageType.VOICE_DATA, data).send(self.s)
            except KeyboardInterrupt:
                raise
            except ConnectionResetError:
                print(f'Server closed the connection')
                self.s.close()
                exit(1)
            except BaseException as e:
                logger.error(e)


client = Client()
