#!/usr/bin/python3

import json
import threading
import socket

from loguru import logger

from protocol import Message, MessageType


class Client:
    def __init__(self, username: str, room_id: str, socket: socket.socket, lock):
        self.username = username
        self.room_id = room_id
        self.socket = socket
        self.lock = lock
        self.talking = False

    def read_message(self):
        with self.lock:
            return Message.read_message(self.socket)

    def send_message(self, message):
        with self.lock:
            message.send(self.socket)


class Server:
    def __init__(self):
        self.ip = socket.gethostbyname(socket.gethostname())
        while True:
            try:
                self.port = int(input('Enter port number to run on --> '))

                self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.s.bind((self.ip, self.port))

                break
            except OSError as e:
                print(e)

        self.rooms = {}
        self.lock = threading.Lock()
        self.accept_connections()

    def accept_connections(self):
        logger.info(f'Running on IP: {self.ip}')
        logger.info(f'Running on port: {self.port}')

        self.s.listen(100)

        while True:
            c, addr = self.s.accept()
            logger.info(f'Received connection from {addr}')

            threading.Thread(target=self.register_client, args=(c, addr, self.rooms)).start()

    def broadcast(self, room: dict[str, Client], message: Message):
        for client in room.values():
            try:
                client.send_message(message)
            except BaseException as e:
                logger.error(e)

    @logger.catch
    def register_client(self, c, addr, rooms):
        while True:
            logger.info(f'Waiting for client {addr}')

            m = Message.read_message(c)
            d = json.loads(m.content)
            username = d['username']
            room_id = d['room_id']

            with self.lock:
                if room_id not in rooms:
                    rooms[room_id] = {}
            room = rooms[room_id]

            if username in room:
                Message.build_message(MessageType.CONNECTION_RESPONSE, json.dumps(
                    {'result': 'error', 'reason': 'That username is already in use in this room'})).send(c)
                logger.info(f'Username {username} already in use in room {room_id}')
                continue

            with self.lock:
                rooms[room_id][username] = Client(username, room_id, c, threading.Lock())

            Message.build_message(MessageType.CONNECTION_RESPONSE, json.dumps(
                {'result': 'ok'})).send(c)
            break
        logger.success(f'Client @{username} at {addr} entered room {room_id}')

        with self.lock:
            d = {username: client.talking for username, client in rooms[room_id].items()}
        self.broadcast(room, Message.build_message(MessageType.ROOM_STATE, json.dumps(d)))

        while True:
            m = rooms[room_id][username].read_message()
            logger.trace(f'Read message {m} from client @{username}')
            if m.message_type is MessageType.VOICE_DATA:
                self.broadcast(room, m)
                continue
            elif m.message_type is MessageType.START_TALKING:
                rooms[room_id][username].talking = True
            elif m.message_type is MessageType.STOP_TALKING:
                rooms[room_id][username].talking = False
            elif m.message_type is MessageType.DISCONNECT:
                rooms[room_id][username].socket.close()
                rooms[room_id].pop(username, None)
                break
            with self.lock:
                d = {username: client.talking for username, client in rooms[room_id].items()}
            self.broadcast(room, Message.build_message(MessageType.ROOM_STATE, json.dumps(d)))


server = Server()
