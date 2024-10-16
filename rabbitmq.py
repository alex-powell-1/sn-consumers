from datetime import datetime
from traceback import format_exc as tb

import pika.exceptions
from error_handler import ProcessInErrorHandler
import pika
import sys
import time
import os

host = os.getenv('RABBITMQ_HOST')


class RabbitMQConsumer:
    def __init__(self, queue_name, callback_func, host=host, eh=ProcessInErrorHandler):
        self.eh = eh
        self.logger = self.eh.logger
        self.error_handler = self.eh.error_handler
        self.queue_name = queue_name
        self.host = host
        self.connection = None
        self.channel = None
        self.callback_func = callback_func

    def connect(self):
        parameters = pika.ConnectionParameters(self.host)
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.queue_name, durable=True)

    def callback(self, ch, method, properties, body):
        body = body.decode()
        self.logger.info(f'{self.queue_name}: Received: {body}')
        try:
            self.callback_func(body, eh=self.eh)
        except Exception as err:
            error_type = 'Exception:'
            self.error_handler.add_error_v(
                error=f'Error ({error_type}): {err}', origin=self.queue_name, traceback=tb()
            )
        else:
            self.logger.success(f'Processing Finished at {datetime.now():%H:%M:%S}\n')
        finally:
            ch.basic_ack(delivery_tag=method.delivery_tag)
            self.error_handler.print_errors()

    def start_consuming(self):
        try:
            self.connect()
            self.channel.basic_consume(queue=self.queue_name, on_message_callback=self.callback)
            print(f'Log Directory Contents {os.listdir('./logs/')})')
            self.logger.info(f'Consumer {self.queue_name}: Waiting for messages. To exit press CTRL+C')
            self.channel.start_consuming()
        except KeyboardInterrupt:
            sys.exit(0)
        # Don't recover if connection was closed by broker
        except pika.exceptions.ConnectionClosedByBroker:
            self.error_handler.add_error_v('Connection closed by broker, retry connection')
        # Don't recover on channel errors
        except pika.exceptions.AMQPChannelError:
            self.error_handler.add_error_v('Channel error, retry connection')
        # Don't recover on stream errors
        except pika.exceptions.StreamLostError:
            self.error_handler.add_error_v('Stream error, retry connection')
        # Recover on all other connection errors
        except pika.exceptions.AMQPConnectionError:
            self.error_handler.add_error_v('Connection error, retry connection')
        except Exception as err:
            self.error_handler.add_error_v(error=err, origin=self.queue_name, traceback=tb())
            time.sleep(5)  # Wait before attempting reconnection
