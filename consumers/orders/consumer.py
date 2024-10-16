import time
from error_handler import ProcessInErrorHandler
from consumers.orders.order import Order
from rabbitmq import RabbitMQConsumer
import creds


def process_order(order_id, eh=ProcessInErrorHandler):
    eh.logger.info(f'Beginning processing for Order #{order_id}')
    time.sleep(5)  # <-- This is to give payment processor time to complete
    Order(order_id).process()


consumer = RabbitMQConsumer(queue_name=creds.Consumer.orders, callback_func=process_order, eh=ProcessInErrorHandler)
consumer.start_consuming()
