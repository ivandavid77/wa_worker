import logging
import os
import json
import sys
import messenger


def parse_body(body):
    ''' "body" must be structured like:
    {
        "phones": ["5212287779788", "5212287779789"],
        "mails": ["ivandavid77@gmail.com","dbarron@crediland.com.mx"]
        "msg": "algun mensaje#13con varias#13lineas"
    } '''
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
    return _json['phones'], _json['mails'], _json['msg'].replace('#13', '\n')


def callback(ch, method, properties, body):
    try:
        phones, mails, msg = parse_body(body)
        logging.debug('Trying to send message...')
        try:
            messenger.send(phones, mails, msg)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logging.debug('Message was processed')
        except Exception as e:
            logging.warn('Sending problem: %r' % (str(e),))
            logging.debug('Message was NOT processed')
    except Exception as e:
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logging.error('Message discarted because error parsing json: %r' % (
            str(e),))


def init_logger(log_name, debug=False):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(format='[%(asctime)s] %(levelname)s : %(message)s',
        datefmt='%d/%m/%Y %I:%M:%S %p', level=level, filename=log_name)


if __name__ == '__main__':
    debug = True if len(sys.argv) == 2 and sys.argv[1] == '-d' else False
    init_logger(os.path.join(os.path.dirname(__file__), 'start.log'), debug)
    sys.path.append(os.path.join(os.getenv('MOUNT_POINT'), 'wa_worker'))
    from wa_worker.base.bootstrap import start
    start('MQ_SEND_MESSAGE_QUEUE', callback)
