# thugd.py - DistributedThug class used for simplifying the
#   interaction between thugboss and thuglets with rabbitmq.
import argparse
import chardet
import configparser
import json
import logging
import pika
import requests
import sys
import time

console_r = lambda s: "\033[91m{}\033[0m".format(s)
console_g = lambda s: "\033[92m{}\033[0m".format(s)
console_y = lambda s: "\033[93m{}\033[0m".format(s)

def decode(data):
    if isinstance(data, bytes):
        c = chardet.detect(data)
        data = data.decode(c["encoding"], errors="replace")
    return data

class DistributedThug(object):
    def __init__(self, config):
        """
        @config: config file
        """
        self._load_config(config)
        self.connect()

    @property
    def task_count(self):
        return self.task_qs.method.message_count

    @property
    def resp_count(self):
        return self.resp_qs.method.message_count

    def __del__(self):
        if self.connection:
            self.connection.close()

    def _load_config(self, config):
        cfg = configparser.ConfigParser()
        cfg.read(config)
        self.hostname = cfg.get("rabbitmq", "hostname")
        self.username = cfg.get("rabbitmq", "username")
        self.password = cfg.get("rabbitmq", "password")
        self.task_queue = cfg.get("rabbitmq", "task_queue")
        self.resp_queue = cfg.get("rabbitmq", "resp_queue")
        self.skip_queue = cfg.get("rabbitmq", "skip_queue")

    def connect(self):
        """
        connection and queue preparation with multiple connection attempts
        """
        while True:
            try:
                # amqp connection attempt
                credentials = pika.PlainCredentials(self.username, self.password)
                parameters = pika.ConnectionParameters(
                    host = self.hostname,
                    credentials = credentials,
                    heartbeat_interval = 0
                )
                self.connection = pika.BlockingConnection(parameters)
                self.channel = self.connection.channel()
                break
            except pika.exceptions.ConnectionClosed:
                log = console_r("! Failed to connect. Trying again.")
                logging.warn(log)
                time.sleep(3)

        # declare queues
        self.task_qs = self.channel.queue_declare(queue=self.task_queue, durable=True)
        self.resp_qs = self.channel.queue_declare(queue=self.resp_queue, durable=True)
        self.resp_qs = self.channel.queue_declare(queue=self.skip_queue, durable=True)
        self.channel.basic_qos(prefetch_count=1)

    def publish(self, message, routing_key):
        """
        publish message to channel

        @message: dict that is converted to json string
        @routing_key: queue name to send the message to
        """
        message = decode(message)
        body = json.dumps(message, ensure_ascii=False)
        persistent = pika.BasicProperties(delivery_mode=2)
        self.channel.basic_publish(
            body = body,
            exchange = "",
            properties = persistent,
            routing_key = routing_key
        )

    def consume(self, callback, queue):
        """
        continuously consume messages from the queue

        @callback: callback function to process messages
        @queue: queue to retrieve messages from
        """
        self.channel.basic_consume(callback, queue=queue)
        self.channel.start_consuming()

    def consume_one(self, queue):
        """
        attempt to consume a single message from the queue

        @queue: queue to retrieve message from
        """
        method, properties, body = self.channel.basic_get(queue)
        if method:
            self.channel.basic_ack(method.delivery_tag)
            return body
