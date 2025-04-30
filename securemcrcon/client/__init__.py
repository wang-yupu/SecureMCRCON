#
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable


class RCONClient(ABC):
    @abstractmethod
    def connect(self, hostname: str, port: int, password: str, skipAuth: bool = False) -> bool:
        ...

    @abstractmethod
    def sendCommand(self, command: str) -> str:
        ...

    @abstractmethod
    def chat(self, message: str) -> None:
        ...

    @abstractmethod
    def setChat(self) -> None:
        ...

    @abstractmethod
    def setChatCallback(self, callback: Callable) -> None:
        ...
