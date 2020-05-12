from __future__ import absolute_import, unicode_literals
from celery.decorators import task
from celery import current_task
from . import models

import warnings
warnings.filterwarnings('ignore',category=FutureWarning)

import sys
import iptc
import pickle
import socket
import logging
import datetime
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
    lv_directory = os.path.dirname('sniff/logs/')
    if not os.path.exists(lv_directory):
        os.makedirs(lv_directory)
    lv_logger = logging.getLogger(__name__)
    lv_hdlr = logging.FileHandler('sniff/logs/' + datetime.now().strftime("%Y%m%d_%H%M") + '.log')
    lv_formatter = logging.Formatter('%(asctime)s - %(message)s')
    lv_hdlr.setFormatter(lv_formatter)
    lv_logger.addHandler(lv_hdlr)
    lv_logger.setLevel(logging.INFO)
    return lv_logger

def checker(iv_qname, iv_ip_src, iv_ip_dst):
    gv_pre_domain = None
    lv_ext_qname = tldextract.extract(iv_qname)
    # Преобразование домена в последовательность int с одиннаковой длиной.
    lv_seq = list(lv_ext_qname.domain)
    lv_x_pred = [gv_valid_chars[y] for y in lv_seq]
    lv_x_pred = sequence.pad_sequences([lv_x_pred], maxlen=gv_maxlen)
    gv_pre_domain = lv_ext_qname.domain
    # Предсказание типа доменного имени.
    with gv_session.as_default():
        with gv_graph.as_default():
            lv_pred_class = gv_model.predict_classes(lv_x_pred)[0][0]
            lv_pred_proba = gv_model.predict_classes(lv_x_pred)[0][0]

    if lv_pred_class == 0:
        lv_n_class = 'Legit'
    else:
        lv_n_class = 'DGA'

    # current_task.update_state(state='PROGRESS', meta={'step' : 'Domain class: ' + lv_n_class + ', Route: ' + iv_ip_src + ' --> ' + iv_ip_dst + ', QNAME: ' + iv_qname})

    lv_pred_family = None
    lv_pred_family_prob = None

    if lv_pred_class == 1:
        # Предсказание подтипа DGA доменного имени.
        with gv_session.as_default():
            with gv_graph.as_default():
                lv_pred_subclass = gv_model_dga.predict_classes(lv_x_pred)
                lv_pred_subproba = gv_model_dga.predict_proba(lv_x_pred)
                lv_pred_family = gv_family_dict[lv_pred_subclass[0]]
                lv_pred_family_prob = lv_pred_subproba[0][lv_pred_subclass[0]]
        # Сохранение в логах
        gv_logger.info(iv_ip_src + ' --> ' + iv_ip_dst + ' : ' + iv_qname)
    # Сохранение в базе
    lv_req = models.Requests(ip_dst=iv_ip_dst, ip_src=iv_ip_src, qname=iv_qname, dga=lv_pred_class, dga_proba=lv_pred_proba, dga_subtype=lv_pred_family, dga_subtype_proba = lv_pred_family_prob)
    lv_req.save()


def packet_callback(iv_packet):
    # Отсеивание выходящих пакетов
    if IP in iv_packet and iv_packet[IP].src != gv_interface_ip:
        lv_ip_src = iv_packet[IP].src
        lv_ip_dst = iv_packet[IP].dst
        # Нахождение dns запросов, извлечение запрашиваемого домена.
        if iv_packet.haslayer(DNS) and iv_packet.getlayer(DNS).qr == 0:
            lv_qname = iv_packet.getlayer(DNS).qd.qname.decode("utf-8")
            # Проверка dns запроса.
            checker(lv_qname, lv_ip_src, lv_ip_dst)


def sendTCP(iv_dns_up_ip, iv_query):
    # Отправка tcp запросов на вышестоящий dns сервер.
    lv_server = (iv_dns_up_ip, 53)
    lv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lv_sock.connect(lv_server)

    # Перестройка tcp запроса на основе udp.
    lv_pay = chr(len(iv_query))
    lv_tcp_query = b'\x00' + lv_pay.encode() + iv_query

    lv_sock.send(lv_tcp_query)  	
    lv_data = lv_sock.recv(1024)
    return lv_data


def handler(iv_data, iv_addr, iv_socket, iv_dns_up_ip, iv_interface):
    # Новый поток для обработки udp запроса на tcp запрос.
    lv_TCPanswer = sendTCP(iv_dns_up_ip, iv_data)
    lv_UDPanswer = lv_TCPanswer[2:]
    iv_socket.sendto(lv_UDPanswer, iv_addr)

    # Извлечение запрашиваемого домена, ip адресов.
    lv_ip_src = iv_addr[0]
    lv_ip_dst = gv_interface_ip
    lv_layerDNS = DNS(iv_data)
    lv_qname = lv_layerDNS.qd.qname.decode("utf-8")

    # Проверка dns запроса.
    checker(lv_qname, lv_ip_src, lv_ip_dst)


@task(name="capture")
def task_capture(iv_interface, iv_as_proxy=False, iv_dns_up_ip=None, iv_port=None):
    global gv_model
    global gv_model_dga
    global gv_valid_chars
    global gv_family_dict
    global gv_maxlen
    global gv_logger
    global gv_interface_ip
    global gv_session
    global gv_graph
    global gv_pre_domain

    current_task.update_state(state='PROGRESS', meta={'step' : 'loading dga prediction model from disk...'})
    with CustomObjectScope({'GlorotUniform': glorot_uniform()}):
        gv_model = load_model('get_model/input_data/dga_prediction_model.h5')

    current_task.update_state(state='PROGRESS', meta={'step' : 'loading family prediction model from disk...'})
    with CustomObjectScope({'GlorotUniform': glorot_uniform()}):
        gv_model_dga = load_model('get_model/input_data/family_prediction_model.h5')

    current_task.update_state(state='PROGRESS', meta={'step' : 'loading data for models...'})
    with open('get_model/input_data/training_data.pkl', 'rb') as f:
        lv_training_data = pickle.load(f)
    lv_all_data_dict = pd.concat([lv_training_data['legit'][:100000], lv_training_data['dga'][:100000]], 
                                ignore_index=False, sort=True)
    gv_family_dict = {idx:x for idx, x in enumerate(lv_training_data['dga']['family'].unique())}
    lv_x = np.array(lv_all_data_dict['domain'].tolist())
    gv_valid_chars = {x:idx+1 for idx, x in enumerate(set(''.join(lv_x)))}
    gv_maxlen = np.max([len(x) for x in lv_x])

    current_task.update_state(state='PROGRESS', meta={'step' : 'warming-up models...'})
    gv_model.predict(np.array([np.zeros(gv_maxlen, dtype=int)]))
    gv_model_dga.predict(np.array([np.zeros(gv_maxlen, dtype=int)]))
    gv_session = K.get_session()
    gv_graph = tf.get_default_graph()
    gv_graph.finalize()

    gv_logger = logger_setup()
    gv_logger.info("Запросы содержащие DGA-домены:")
    
    # Получение ip адреса интерфейса.
    lv_addr = ni.ifaddresses(iv_interface)
    gv_interface_ip = lv_addr[ni.AF_INET][0]['addr']
    
    current_task.update_state(state='PROGRESS', meta={'step' : 'capturing requests...'})
    # Основной процесс, сканирование сети.
    if iv_as_proxy == True:
        lv_host = ''
        # Настройка udp сервера для получения dns запросов.
        lv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        lv_sock.bind((lv_host, iv_port))
        while True:
            lv_data, lv_addr = lv_sock.recvfrom(1024)
            lv_th = Thread(target=handler, args=(lv_data, lv_addr, lv_sock, iv_dns_up_ip, iv_interface))
            lv_th.start()

            # Put in view to safety close socket thread
            # lv_sock.close()

    else: sniff(iface=iv_interface, filter="port 53", store=0, prn=packet_callback)

    return {'step' : 'success'}
