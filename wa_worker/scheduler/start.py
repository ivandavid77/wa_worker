import logging
import os
import json
import sys
import logging
import pika
import crontab
import taskstore


def parse_add(_json):
    if not 'task_name' in _json:
        raise Exception('"task_name" was not specified')
    if not 'phones' in _json:
        raise Exception('"phones" was not specified')
    if not 'mails' in _json:
        raise Exception('"mails" was not specified')
    if not 'cron' in _json:
        raise Exception('"cron" was not specified')
    if not 'sql' in _json:
        raise Exception('"sql" was not specified')
    if not type(_json['task_name']) in (str, bin, unicode):
        raise Exception('"task_name" must be a text')
    if type(_json['phones']) != list:
        raise Exception('"phones" must be list')
    if type(_json['mails']) != list:
        raise Exception('"mails" must be list')
    if not type(_json['cron']) in (str, bin, unicode):
        raise Exception('"cron" must be a text')
    if not type(_json['sql']) in (str, bin, unicode):
        raise Exception('"msg" must be a text')
    return {
            'task_name': _json['task_name'],
            'phones': _json['phones'],
            'mails': _json['mails'],
            'cron': _json['cron'],
            'sql': _json['sql'].replace('#13', '\n')
        }


def parse_body(body):
    ''' "body" must be structured like:
    {
        "operation": "add" or "rm" or "status"

        if operation == "add" then next keys must defined:
        "task_name": "a unique name for task",
        "phones": ["5212287779788", "5212287779789"],
        "mails": ["ivandavid77@gmail.com","dbarron@crediland.com.mx"],
        "cron": "0 9-21/1 * * *",
        "sql": "some sql#13to execute;#13many queries#13separated by;"
    } '''
    try:
        _json = json.loads(body)
    except ValueError as e:
        logging.error('Malformed json: \n %s' % (str(e),))
        raise Exception('Malformed string')
    if not 'operation' in _json:
        raise Exception('"operation" was not specified')
    if _json['operation'] == 'add':
        return 'add', parse_add(_json)


def handle_operation(op, data):
    if op == 'add':
        return taskstore.add_task(
            data['task_name'],
            data['cron'],
            data['phones'],
            data['mails'],
            data['sql'])


def callback(ch, method, props, body):
    try:
        operation, data = parse_body(body)
        handle_operation(operation, data)
        logging.debug('Message was processed')
        result = '{"result": "sucess"}'
    except Exception as e:
        error = 'Message discarted : %r' % (str(e),)
        result = '{"result": "error", "msg" : "%s"}' % (error,)
        logging.error(error)
    ch.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(correlation_id =
                                                     props.correlation_id),
                     body=result)
    ch.basic_ack(delivery_tag=method.delivery_tag)


def init_logger(log_name, debug=False):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(format='[%(asctime)s] %(levelname)s : %(message)s',
        datefmt='%d/%m/%Y %I:%M:%S %p', level=level, filename=log_name)


if __name__ == '__main__':
    debug = True if len(sys.argv) == 2 and sys.argv[1] == '-d' else False
    init_logger(os.path.join(os.path.dirname(__file__), 'start.log'), debug)
    sys.path.append(os.path.join(os.getenv('MOUNT_POINT'), 'wa_worker'))
    from wa_worker.base.bootstrap import start
    start('MQ_TASK_MANAGEMENT_QUEUE', callback)
