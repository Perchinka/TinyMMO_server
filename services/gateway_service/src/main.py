from src.config import Config
from confluent_kafka import Producer, Consumer
from pydantic import BaseModel

import socket
import logging
import threading

from abc import ABC, abstractmethod
from src.packets import from_json, ChatPacket

class ChatMsg(BaseModel):
    to_id: int
    from_id: int
    content: str

class KafkaAdapter(ABC):
    @abstractmethod
    def publish(self, msg: ChatMsg):
        raise NotImplementedError

    @abstractmethod
    def consume(self):
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
    
    def publish(self, user_id: int, connected: bool):
        self.producer.produce('connections', key=str(user_id).encode('utf-8'), value=str(connected).encode('utf-8'))
    
    def consume(self):
        pass
    

class Worker:
    def __init__(self, config: Config):
        self.config = config
        self.chat_kafka = ChatKafkaAdapter(self.config)
        self.connections_kafka = ConnectionsKafkaAdapter(self.config)
        
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.mapping_dict = {} # Probably not the best way to store user_id:connections pairs but it's good enough for now

    def run(self):
        self.server_socket.bind((self.config.LISTENER_HOST, self.config.LISTENER_PORT))
        self.server_socket.listen()
        logging.info('Server is listening on {}:{}'.format(self.config.LISTENER_HOST, self.config.LISTENER_PORT))

        # Just for now, while I don't have database and initialization logic
        self.user_id = 0

        # Start polling messages from Kafka and sending them to the clients
        threading.Thread(target=self.poll_messages).start()
        while True:
            conn, addr = self.server_socket.accept()

            try:
                threading.Thread(target=self.handle_connection, args=(conn, self.user_id)).start()
                self.connections_kafka.publish(self.user_id, True)
                self.mapping_dict[self.user_id] = conn
                self.user_id += 1
            except Exception as e:
                logging.error('Error handling connection: {}'.format(e))
                self.connections_kafka.publish(self.user_id, False)
                conn.close()
    
    def handle_connection(self, conn: socket.socket, user_id: int):
        logging.info('Connection enstablished with user{}'.format(user_id))
        while True:
            data = conn.recv(1024)

            if not data:
                self.connections_kafka.publish(user_id, False)
                del self.mapping_dict[user_id]
                conn.close()
                logging.info('Connection closed with user{}'.format(user_id))
                break

            packet = from_json(data.decode('utf-8'))
            if packet is None:
                continue
            
            logging.info('Received {}Packet from {} \n\t {}'.format(packet.packet_type.name, user_id, str(packet)))
            if packet.packet_type.name == 'Chat':
                self.chat_kafka.publish(ChatMsg(to_id=packet.to_id, from_id=packet.from_id, content=packet.content))
        
    
    def poll_messages(self):
        while True:
            packet = self.chat_kafka.consume()
            if packet is None:
                continue
            logging.info('Received ChatPacket from Kafka: {}'.format(packet))
            conn = self.mapping_dict.get(packet.to_id)
            if conn is None:
                logging.error('Connection not found for user {}'.format(packet.to_id))
                continue
            conn.send(bytes(packet))
            logging.info('Sent ChatPacket to {}:{}'.format(conn.getpeername()[0], conn.getpeername()[1])) 
            


if __name__ == '__main__':
    config = Config()
    worker = Worker(config)
    worker.run()