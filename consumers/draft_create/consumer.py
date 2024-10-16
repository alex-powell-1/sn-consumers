import rabbitmq
import creds
import error_handler
from consumers.orders.draft_orders import on_draft_created


consumer = rabbitmq.RabbitMQConsumer(
    queue_name=creds.Consumer.draft_create, callback_func=on_draft_created, eh=error_handler.ProcessInErrorHandler
)
consumer.start_consuming()
