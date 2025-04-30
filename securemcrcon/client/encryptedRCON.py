from . import RCONClient
from securemcrcon.utils.packet import *
import socket as socketLib
import securemcrcon.utils.exchange as exchange
import base64
from cryptography.hazmat.primitives import serialization
from securemcrcon.utils import encrypt
import threading
from typing import Callable

__all__ = ['EncryptedRCON']


class EncryptedRCON(RCONClient):
    socket: socketLib.socket | None = None
    packetID = 0
    encrypted = False
    inChat: bool = False
    chatCallback: Callable | None = None
    publicKeyHash: bytes | None = None

    def send(self, data: bytes | RCONPacket) -> None:
        if self.socket:
            if isinstance(data, RCONPacket):
                d = packetClassToRaw(data)
            else:
                d = data
            if self.encrypted:
                encryptedData = encrypt.ChaCha20Poly1305Encrypt(d, self.key, None, self.packetID)
                self.socket.send(encryptedData)
            else:
                self.socket.send(d)
            self.packetID += 1
        else:
            raise Exception("No connection")

    def recv(self, bufsize=2048) -> None | RCONPacket | bytes:
        if self.socket:
            data = self.socket.recv(bufsize)
            if self.encrypted:
                try:
                    data = encrypt.ChaCha20Poly1305Decrypt(data, self.key, None, self.packetID)
                except Exception as e:
                    raise ValueError(f"Decrypt failed: {e}")
            try:
                return rawToPacketClass(data)
            except ValueError:
                return data
        else:
            raise Exception("No connection")

    def connect(self, hostname, port, password, skipAuth: bool = False) -> bool:
        self.clientPrivate, self.clientPublic = exchange.newKeyPair()
        self.socket = socketLib.socket()
        self.socket.connect((hostname, port))
        # exchange pkey
        self.send(RCONPacket(0, self.packetID, 255, b""))
        exchangePublicResult = self.recv()
        if not exchangePublicResult:
            raise Exception(f"Failed to encrypt connect. Maybe server does not support encrypt.")
        if not isinstance(exchangePublicResult, RCONPacket):
            raise Exception(f"Failed to encrypt connect. Maybe server does not support encrypt.")
        # 接收服务端公钥
        serverPublic = exchange.x25519.X25519PublicKey.from_public_bytes(
            base64.b85decode(exchangePublicResult.payload))
        self.key = exchange.exchange(self.clientPrivate, serverPublic, None, b'INFO', 32)
        # 发自己的公钥
        self.send(RCONPacket(0, self.packetID, 255, self.clientPublic.public_bytes(encoding=serialization.Encoding.Raw,
                                                                                   format=serialization.PublicFormat.Raw)))
        self.encrypted = True
        self.packetID = 0
        self.publicKeyHash = exchange.publicToHash(serverPublic)

        # auth
        if not skipAuth:
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

    def getPublicKeyHash(self) -> bytes:
        if self.publicKeyHash:
            return self.publicKeyHash
        else:
            return b''

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
