import os
from kombu import serialization, Exchange, Queue

broker=os.environ.get('BROKER_URL','amqp://guest@localhost//'),
backend=os.environ.get('BACKEND_URL', 'rpc://'),
accept_content = ['json']
task_serializer = 'json'
result_serializer = 'json'
serialization.register_json()
serialization.enable_insecure_serializers()
enable_utc=True
task_queues= [Queue(
        os.environ.get('SUBMISSION_QUEUE', 'submission-queue'), 
        exchange=Exchange(os.environ.get('SUBMISSION_EXCHANGE','submission-exchange'), 
        type='direct', routing_key='submit'))]
root_path=os.path.dirname(os.path.abspath(__file__))