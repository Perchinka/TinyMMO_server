from src.config import Config
from confluent_kafka import Producer, Consumer
from pydantic import BaseModel

import socket
import logging
import threading

from abc import ABC, abstractmethod

from src.packets import ChatPacket

class ChatMsg(BaseModel):
    to_id: int
    from_id: int
    content: str

class KafkaAdapter(ABC):
    @abstractmethod
    def publish(self, msg: ChatMsg):
        raise NotImplementedError

    @abstractmethod
    def consume(self) -> ChatPacket:
        raise NotImplementedError
    

class ChatKafkaAdapter:
    def __init__(self, config: Config):
        self.producer = Producer({
            'bootstrap.servers': config.KAFKA_URL,
            'client.id': socket.gethostname()
        })
        self.consumer = Consumer({
            'bootstrap.servers': config.KAFKA_URL,
            'group.id': 'chat-service',
        })
    
    def publish(self, msg: ChatMsg):
        self.producer.produce('rcv', key=str(msg.to_id), value="{} ; {}".format(msg.from_id, msg.content).encode('utf-8'))
        logging.info('Message published: {}'.format(msg))
    
    def consume(self) -> ChatPacket:
        self.consumer.subscribe(['snd'])
        msg = self.consumer.poll()
        if msg is None:
            return None
        if msg.error():
            logging.error('Consumer error: {}'.format(msg.error()))
            return None
            
        to_id = int(msg.key().decode('utf-8'))
        from_id, content = msg.value().decode('utf-8').split(';', 1)
        return ChatPacket(to_id, from_id, content)

class ConnectionsKafkaAdapter:
    def __init__(self, config: Config):
        self.producer = Producer({
            'bootstrap.servers': config.KAFKA_URL,
            'client.id': socket.gethostname()
        })
        self.consumer = Consumer({
            'bootstrap.servers': config.KAFKA_URL,
            'group.id': 'connections',
        })
    
    def publish(self, address: str, connected: bool):
        self.producer.produce('connections', key=address, value=str(connected).encode('utf-8'))
    
    def consume(self):
        pass
    

class Worker:
    def __init__(self):
        self.config = Config()
        self.chat_kafka = ChatKafkaAdapter(self.config)
        self.connections_kafka = ConnectionsKafkaAdapter(self.config)
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.mapping_dict = {}

    def run(self):
        self.server_socket.bind((self.config.LISTENER_HOST, self.config.LISTENER_PORT))
        self.server_socket.listen()
        logging.info('Server is listening on {}:{}'.format(self.config.LISTENER_HOST, self.config.LISTENER_PORT))
        while True:
            conn, addr = self.server_socket.accept()

            try:
                threading.Thread(target=self.handle_connection, args=(conn, addr)).start()
                self.connections_kafka.publish(addr[0], True)
                self.mapping_dict[addr] = conn
            except Exception as e:
                logging.error('Error handling connection: {}'.format(e))
                self.connections_kafka.publish(addr[0], False)
                conn.close()
    
    def handle_connection(self, conn: socket.socket, addr: tuple[str, int]):
        logging.info('Connection enstablished with {}:{}'.format(addr[0], addr[1])) 
        
        while True:
            data = conn.recv(1024)

            if not data:
                self.connections_kafka.publish(addr[0], False)
                del self.mapping_dict[addr]
                conn.close()
                logging.info('Connection closed with {}:{}'.format(addr[0], addr[1]))
                break
            
            logging.info('Received message from {}:{} - {}'.format(addr[0],addr[1], data))


if __name__ == '__main__':
    worker = Worker()
    worker.run()