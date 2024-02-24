from src import Config
from confluent_kafka import Producer, Consumer, KafkaError

class KafkaAdapter:
    def __init__(self):
        self.producer = Producer({
            'bootstrap.servers': Config.KAFKA_URL,
            'sasl.mechanisms': 'PLAIN',
            'security.protocol': 'SASL_SSL',
            'sasl.username': Config.KAFKA_USERNAME,
            'sasl.password': Config.KAFKA_PASSWORD
        })
        self.consumer = Consumer({
            'bootstrap.servers': Config.KAFKA_URL,
            'sasl.mechanisms': 'PLAIN',
            'security.protocol': 'SASL_SSL',
            'sasl.username': Config.KAFKA_USERNAME,
            'sasl.password': Config.KAFKA_PASSWORD,
            'group.id': 'chat_service',
            'auto.offset.reset': 'earliest'
        })
    
    def produce(self, topic, message):
        self.producer.produce(topic, message)
        self.producer.flush()
    
    def consume(self, topic):
        self.consumer.subscribe([topic])
        while True:
            msg = self.consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    print(msg.error())
                    break
            print('Received message: {}'.format(msg.value().decode('utf-8')))
        self.consumer.close()