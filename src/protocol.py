from __future__ import annotations

import socket
from enum import Enum, auto
from loguru import logger
from typing import Union
import struct
import pydantic


def recvall(socket, length):
    data = b''
    while len(data) < length:
        data += socket.recv(length - len(data))
    return data


class MessageType(Enum):
    CONNECTION_REQUEST = auto()
    CONNECTION_RESPONSE = auto()
    VOICE_DATA = auto()
    START_TALKING = auto()
    STOP_TALKING = auto()
    ROOM_STATE = auto()
    DISCONNECT = auto()


class Message(pydantic.BaseModel):
    message_type: MessageType
    content_length: int
    content: bytes

    @classmethod
    def read_message(cls, s: socket.socket) -> Message:
        try:
            header = recvall(s, 8)
            message_type_int, content_length = struct.unpack('!II', header)
            content = recvall(s, content_length)
            message_type = MessageType(message_type_int)
        except ConnectionResetError:
            raise
        return cls(message_type=message_type, content_length=content_length, content=content)

    @classmethod
    def build_message(cls, message_type: MessageType, content: Union[str, bytes]) -> Message:
        if isinstance(content, str):
            content_bytes = content.encode('utf-8')
        elif isinstance(content, bytes):
            content_bytes = content
        else:
            raise ValueError
        content_length = len(content_bytes)
        return cls(message_type=message_type, content_length=content_length, content=content)

    def send(self, s: socket.socket):
        header = struct.pack('!II', int(self.message_type.value), len(self.content))
        data = header + self.content
        s.sendall(data)
