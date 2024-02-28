from enum import Enum
import logging
import json

class PacketType(Enum):
    Chat = 0

class Packet:
    def __init__(self, packet_type: PacketType, *payloads: tuple):
        self.packet_type = packet_type
        self.payloads: tuple = payloads
    
    def __str__(self) -> str:
        serialized = {'a': self.packet_type.value}
        for i, payload in enumerate(self.payloads):
            serialized[f'p{i}'] = payload
        data = json.dumps(serialized)
        return data

    def __bytes__(self) -> bytes:
        return str(self).encode('utf-8')

    
def from_json(data: str) -> Packet:
    try:
        deserialized = json.loads(data)
    except json.JSONDecodeError as e:
        logging.error(f'Error deserializing packet: {e}')
        return None
    try:
        packet_type = PacketType(deserialized['a']).name
        payloads = tuple(deserialized[f'p{i}'] for i in range(len(deserialized) - 1))
    except KeyError as e:
        logging.error(f'Packet deserialization error: {e}')
        return None
    

    class_name = packet_type + 'Packet'
    try:
        constructor: type = globals()[class_name]
        return constructor(*payloads)
    except KeyError as e:
        logging.error(f'Packet type {class_name} not found')
        return None
    except TypeError as e:
        logging.error(f'{class_name} can\'t handle arguments {payloads}. Expected {constructor.__init__.__code__.co_varnames[1:]}.')
        return None
    except Exception as e:
        logging.error(f'Error deserializing packet: {e}')
        return None
    

class ChatPacket(Packet):
    def __init__(self, to_id: int, from_id: int, content: str):
        super().__init__(PacketType.Chat, to_id, from_id, content)
        self.to_id = to_id
        self.from_id = from_id
        self.content = content
    
    def __str__(self) -> str:
        return json.dumps({
            'a': self.packet_type.value,
            'p0': self.to_id,
            'p1': self.from_id,
            'p2': self.content
        })
    
    def __bytes__(self) -> bytes:
        return str(self).encode('utf-8')

 