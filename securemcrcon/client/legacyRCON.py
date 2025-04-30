from typing import Callable
from . import RCONClient
from utils.packet import *
import socket as socketLib
import threading

__all__ = ['LegacyRCON  ']


class LegacyRCON(RCONClient):
    socket: socketLib.socket | None = None
    packetID = 0
    inChat: bool = False
    chatCallback: Callable | None = None

    def send(self, data: bytes | RCONPacket) -> None:
        if self.socket:
            if isinstance(data, RCONPacket):
                self.socket.send(packetClassToRaw(data))
            else:
                self.socket.send(data)
            self.packetID += 1
        else:
            raise Exception("No connection")

    def recv(self, bufsize=2048) -> None | RCONPacket | bytes:
        if self.socket:
            data = self.socket.recv(bufsize)
            try:
                return rawToPacketClass(data)
            except ValueError:
                return data
        else:
            raise Exception("No connection")

    def connect(self, hostname, port, password, skipAuth: bool = False) -> bool:
        self.socket = socketLib.socket()
        self.socket.connect((hostname, port))
        if not skipAuth:
            # auth
            self.send(RCONPacket(0, self.packetID, 3, password.encode(encoding='utf-8')))
            result = self.recv()
            if isinstance(result, RCONPacket):
                if result.id == -1:
                    raise Exception(f"Login failed.{' Message: ' if result.payload else ''}{result.payload}")
                return True
            else:
                return False
        else:
            self.socket.close()
        return False

    def sendCommand(self, command: str) -> str:
        self.send(RCONPacket(0, self.packetID, 2, command.encode(encoding='utf-8')))
        result = self.recv()
        if isinstance(result, RCONPacket):
            return result.payload.decode(encoding='utf-8', errors='replace')
        else:
            return 'Failed to execute command.'

    def chat(self, message: str) -> None:
        if self.inChat:
            self.send(RCONPacket(0, self.packetID, 20, message.encode(encoding='utf-8')))

    def setChat(self) -> None:
        if self.inChat:
            self.send(RCONPacket(0, self.packetID, 17, b''))
            self.inChat = False
        else:
            self.send(RCONPacket(0, self.packetID, 16, b''))
            self.inChat = True
            threading.Thread(target=self.chatListen, name="MCRCONChatListener", daemon=True).start()

    def setChatCallback(self, callback: Callable) -> None:
        self.chatCallback = callback

    def chatListen(self):
        while self.inChat:
            d = self.recv()
            if not isinstance(d, RCONPacket):
                continue
            if d.type == 20:
                if self.chatCallback:
                    self.chatCallback(d.payload.decode(encoding='utf-8', errors='replace'))
