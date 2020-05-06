from django.test import RequestFactory, TestCase
from .models import Requests


class SniffTestCase(TestCase):
    def setUp(self):
        # self.factory = RequestFactory()
        self.req = Requests.objects.create(ip_dst='', ip_src='243.19.14.144', qname='ajsfhkjshf.com', dga='1', dga_proba='0.7', dga_subtype='fwefsd', dga_subtype_proba = '0.3')

    def test_requests_models(self):
        req = Requests.objects.get(ip_src='243.19.14.144')
        self.assertEqual(req.qname,'ajsfhkjshf.com')
