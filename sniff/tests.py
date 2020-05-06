from django.test import RequestFactory, TestCase
from .models import Requests


class SniffTestCase(TestCase):
    def setUp(self):
        self.req = Requests.objects.create(ip_dst='68.183.21.239', ip_src='243.19.14.144', qname='ajsfhkjshf.com', dga='1', dga_proba='0.7', dga_subtype='fwefsd', dga_subtype_proba = '0.3')

    def test_requests_models(self):

        # Get qname by ip_src
        req = Requests.objects.get(ip_src='243.19.14.144')

        # Get correct qname
        self.assertEqual(req.qname,'ajsfhkjshf.com')
