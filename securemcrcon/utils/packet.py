from dataclasses import dataclass
import io


@dataclass
class RCONPacket:
    length: int = 0
    id: int = 255
    type: int = 255
    payload: bytes = b''


def rawToPacketClass(raw: bytes) -> RCONPacket:
    data = io.BytesIO(raw)
    result = RCONPacket(0, 0, 0, b"")

    dataLength = len(raw)
    result.length = int.from_bytes(data.read(4), byteorder='little', signed=True)
    if dataLength - 4 != result.length:
        raise ValueError("Bad RCON Packet")

    result.id = int.from_bytes(data.read(4), byteorder='little', signed=True)
    result.type = int.from_bytes(data.read(4), byteorder='little', signed=True)

    # 读取payload
    payloadLength = dataLength - 3*4 - 2

    data.seek(12)
    result.payload = data.read(payloadLength)

    return result


def packetClassToRaw(packet: RCONPacket) -> bytes:
    length = 4 + 4 + 4 + len(packet.payload) + 2

    packet.length = length - 4

    lengthBytes = packet.length.to_bytes(4, byteorder='little', signed=True)
    idBytes = packet.id.to_bytes(4, byteorder='little', signed=True)
    typeBytes = packet.type.to_bytes(4, byteorder='little', signed=True)
    payloadBytes = packet.payload

    return b''.join([lengthBytes, idBytes, typeBytes, payloadBytes, b'\x00'*2])
