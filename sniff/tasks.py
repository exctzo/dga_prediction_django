from __future__ import absolute_import, unicode_literals
from celery.decorators import task
from celery import current_task

import sys
import iptc
import pickle
import socket
import logging
import tldextract
import numpy as np
import pandas as pd
import netifaces as ni
import tensorflow as tf

from threading import Thread
from scapy.all import *
from scapy.layers.dns import DNS
from scapy.layers.inet import IP

from tensorflow.keras.models import load_model

from tensorflow.keras.utils import CustomObjectScope
from tensorflow.keras.initializers import glorot_uniform

from tensorflow.keras.preprocessing import sequence
from tensorflow.keras import backend as K

def logger_setup():
    directory = os.path.dirname('sniff/logs/')
    if not os.path.exists(directory):
        os.makedirs(directory)
    logger = logging.getLogger(__name__)
    hdlr = logging.FileHandler('sniff/logs/' + datetime.now().strftime("%Y%m%d_%H%M") + '.log')
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.INFO)
    return logger

def checker(qname, ip_src, ip_dst):
    global pre_domain
    ext_qname = tldextract.extract(qname)
    # Отсеивание с длиной < 6 и != предыдущему запросу.
    if len(ext_qname.domain) > 6 and ext_qname.domain != pre_domain:
        # Преобразование домена в последовательность int с одиннаковой длиной.
        seq = list(ext_qname.domain)
        X_pred = [valid_chars[y] for y in seq]
        X_pred = sequence.pad_sequences([X_pred], maxlen=maxlen)
        pre_domain = ext_qname.domain
        # Предсказание типа доменного имени.
        with session.as_default():
            with graph.as_default():
                prediction = model.predict_classes(X_pred)
        if prediction == [[1]]:
            current_task.update_state(state='PROGRESS', meta={'step' : ip_src + ' --> ' + ip_dst + ' : ' + qname})
            logger.info(ip_src + ' --> ' + ip_dst + ' : ' + qname)
            # # Проверка ip адреса на повторное вхождение в список dga запросов.
            # if ip_src in dga_hosts:
            #     dga_hosts[ip_src] = dga_hosts[ip_src] + 1
            # # Добавление ip в список потенциальных dga-узлов.
            # else:
            #     dga_hosts[ip_src] = 1


def packet_callback(packet):
    # Отсеивание выходящих пакетов
    if IP in packet and packet[IP].src != interface_ip:
        ip_src = packet[IP].src
        ip_dst = packet[IP].dst
        # Нахождение dns запросов, извлечение запрашиваемого домена.
        if packet.haslayer(DNS) and packet.getlayer(DNS).qr == 0:
            qname = packet.getlayer(DNS).qd.qname.decode("utf-8")
            # Проверка dns запроса.
            checker(qname, ip_src, ip_dst)


def sendTCP(dns_up_ip, query):
    # Отправка tcp запросов на вышестоящий dns сервер.
    server = (dns_up_ip, 53)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(server)

    # Перестройка tcp запроса на основе udp.
    pay = chr(len(query))
    tcp_query = b'\x00' + pay.encode() + query

    sock.send(tcp_query)  	
    data = sock.recv(1024)
    return data


def handler(data, addr, socket, dns_up_ip, interface):
    # Новый поток для обработки udp запроса на tcp запрос.
    TCPanswer = sendTCP(dns_up_ip, data)
    UDPanswer = TCPanswer[2:]
    socket.sendto(UDPanswer, addr)

    # Извлечение запрашиваемого домена, ip адресов.
    ip_src = addr[0]
    ip_dst = interface_ip
    layerDNS = DNS(data)
    qname = layerDNS.qd.qname.decode("utf-8")

    # Проверка dns запроса.
    checker(qname, ip_src, ip_dst)

# @task(name="iptables")
# def iptables(dga_hosts, logger):
#     logger = logger_setup()
#     logger.info("Заблокированные узлы:")

#     for key, val in dga_hosts.items():
#         if val >= 50:
#             print("Блокировка узла с IP: %s" % key)
#             logger.info("IP адрес: %s" % key)
#             chain = iptc.Chain(iptc.Table(iptc.Table.FILTER), "INPUT")
#             rule = iptc.Rule()
#             rule.src = key
#             rule.target = iptc.Target(rule, "DROP")
#             chain.insert_rule(rule)

@task(name="capture")
def task_capture(interface, as_proxy=False, dns_up_ip=None, port=None):
    global model
    global valid_chars
    global maxlen
    global pre_domain
    global logger
    global dga_hosts
    global interface_ip
    global session
    global graph

    current_task.update_state(state='PROGRESS', meta={'step' : 'loading model from disk...'})
    with CustomObjectScope({'GlorotUniform': glorot_uniform()}):
        model = load_model('get_model/input_data/model.h5')

    current_task.update_state(state='PROGRESS', meta={'step' : 'loading data for model...'})
    with open('get_model/input_data/training_data.pkl', 'rb') as f:
        training_data = pickle.load(f)
    all_data_dict = pd.concat([training_data['legit'], training_data['dga']], 
                                ignore_index=False, sort=True)
    X = np.array(all_data_dict['domain'].tolist())
    valid_chars = {x:idx+1 for idx, x in enumerate(set(''.join(X)))}
    max_features = len(valid_chars) + 1
    maxlen = np.max([len(x) for x in X])

    current_task.update_state(state='PROGRESS', meta={'step' : 'warming-up model...'})
    model.predict(np.array([np.zeros(maxlen, dtype=int)]))
    session = K.get_session()
    graph = tf.get_default_graph()
    graph.finalize()

    pre_domain = None

    # # Подсчет вхождений отдельных dga-узлов.
    # dga_hosts = {}

    logger = logger_setup()
    logger.info("Запросы содержащие DGA-домены:")
    
    # Получение ip адреса интерфейса.
    addr = ni.ifaddresses(interface)
    interface_ip = addr[ni.AF_INET][0]['addr']
    
    current_task.update_state(state='PROGRESS', meta={'step' : 'capturing requests...'})
    # Основной процесс, сканирование сети.
    if as_proxy == True:
        host = ''
        # Настройка udp сервера для получения dns запросов.
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((host, port))
        while True:
            data, addr = sock.recvfrom(1024)
            th = Thread(target=handler, args=(data, addr, sock, dns_up_ip, interface))
            th.start()

            # Put to view to safety close socket thread
            # sock.close()

    else: sniff(iface=interface, filter="port 53", store=0, prn=packet_callback)

    return {'step' : 'success'}
