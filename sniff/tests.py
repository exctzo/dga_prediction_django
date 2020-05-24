from django.test import RequestFactory, TestCase
from .models import Request
import socket
import pydig
from threading import Thread
from scapy.all import *
from scapy.layers.dns import DNS
from scapy.layers.inet import IP

class SniffTestCase(TestCase):
    def setUp(self):
        self.req = Request.objects.create(ip_dst='68.183.21.239', ip_src='243.19.14.144', 
            qname='ajsfhkjshf.com', dga='1', dga_proba='0.7', 
            dga_subtype='fwefsd', dga_subtype_proba = '0.3')

    def test_requests_models(self):
        # Получение запроса через ip_src
        req = Request.objects.get(ip_src='243.19.14.144')

        # Проверка корректности полученного доменного имени
        self.assertEqual(req.qname,'ajsfhkjshf.com')

    def SendTCP(iv_dns_up_ip, iv_query):
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


    def Handler(iv_data, iv_addr, iv_socket, iv_dns_up_ip, iv_interface):
        # Новый поток для обработки udp запроса на tcp запрос.
        lv_TCPanswer = SendTCP(iv_dns_up_ip, iv_data)
        lv_UDPanswer = lv_TCPanswer[2:]
        iv_socket.sendto(lv_UDPanswer, iv_addr)

        # Извлечение запрашиваемого домена, ip адресов.
        lv_ip_src = iv_addr[0]
        lv_ip_dst = gv_interface_ip
        lv_layerDNS = DNS(iv_data)
        lv_qname = lv_layerDNS.qd.qname.decode("utf-8")
    
    def test_proxy_requests(self):
        iv_dns_up_ip = '8.8.8.8'
        iv_interface = os.listdir('/sys/class/net/')[1]
        iv_port = 9981
        lv_host = ''
        # Настройка udp сервера для получения dns запросов.
        lv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        lv_sock.bind((lv_host, iv_port))

        lv_data, lv_addr = lv_sock.recvfrom(1024)
        lv_th = Thread(target=Handler, args=(lv_data, lv_addr, lv_sock, iv_dns_up_ip, iv_interface))
        lv_th.start()
        
        resolver = pydig.Resolver(executable='/usr/bin/dig', nameservers=['exctzo.tech',], additional_args=['-p 9981',])
        answ = resolver.query('example.com', 'A')

        assert answ is not None