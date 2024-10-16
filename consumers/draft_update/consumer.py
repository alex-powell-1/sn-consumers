import rabbitmq
import creds
import error_handler
from consumers.orders.draft_orders import on_draft_updated


consumer = rabbitmq.RabbitMQConsumer(
    queue_name=creds.Consumer.draft_update, callback_func=on_draft_updated, eh=error_handler.ProcessInErrorHandler
)
consumer.start_consuming()
