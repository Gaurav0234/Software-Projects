from flask import Flask
from flask import request,jsonify
from kafka import KafkaProducer
from .service.messageService import messageService
import json

app = Flask(__name__)
app.config.from_pyfile('config.py')

messageService = messageService()
producer = KafkaProducer(bootstrap_servers=['192.168.1.9:9092'],
                         value_serializer=lambda v: json.dumps(v).encode('utf-8'))

@app.route('/v1/ds/message', methods=['POST'])
def handle_message():
    message = request.json.get('message')
    result = messageService.processMessage(message)
    serialized_result = result.json()

    producer.send('my-topic', serialized_result)

    return jsonify(vars(result))

@app.route('/', methods=['GET'])
def handle_get():
    return "Hello World!"

if __name__ == "__main__":
    app.run(host="localhost", port=8000, debug=True)