from django.test import RequestFactory, TestCase
from .models import Request

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
