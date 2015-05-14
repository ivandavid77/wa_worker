import os
import sys
import json
import pika
import etcd


if len(sys.argv) < 2:
    body = '''{
        "phones": ["5212287779788"],
        "mails": ["dbarron@crediland.com.mx"],
        "msg": "test with newline#13test again"
    }'''
else:
    body = sys.argv[1]
    try:
        try:
            _json = json.loads(body)
        except ValueError:
            raise Exception('Malformed string')
        if not 'phones' in _json:
            raise Exception('"phones" was not specified')
        if not 'mails' in _json:
            raise Exception('"mails" was not specified')
        if not 'msg' in _json:
            raise Exception('"msg" was not specified')
        if type(_json['phones']) != list:
            raise Exception('"phones" must be list')
        if type(_json['mails']) != list:
            raise Exception('"mails" must be list')
        if not type(_json['msg']) in (str, bin, unicode):
            raise Exception('"msg" must be a text')
    except Exception as e:
        usage = '''Invalid json format: %r,
            try with the next example:
            {
                "phones": ["5212287779788", "5212287779788"],
                "mails": ["dbarron@crediland.com.mx", "ivandavid77@gmail.com"],
                "msg": "test with newline#13test again"
            }''' % (str(e),)
        print(usage)
        sys.exit(1)
etcd_endpoint = os.getenv('ETCD_ENDPOINT', '127.0.0.1')
etcd_port = int(os.getenv('ETCD_PORT', '4001'))
instance = os.getenv('MQ_INSTANCE', '1')
queue = os.getenv('MQ_QUEUE', 'WA_MESSAGE_QUEUE')
client = etcd.Client(host=etcd_endpoint, port=etcd_port)
service = json.loads(client.read('/services/rabbitmq@'+instance).value)
conn = pika.BlockingConnection(
    pika.ConnectionParameters(service['host'],int(service['port'])))
channel = conn.channel()
channel.queue_declare(queue=queue)
channel.basic_publish(exchange='', routing_key=queue, body=body)
conn.close()
