from django.db import models

class Requests(models.Model) :
    ip_dst = models.GenericIPAddressField()
    ip_src = models.GenericIPAddressField()
    qname = models.CharField(max_length=250)
    report_date = models.DateField()
    dga = models.IntegerField()
    dga_proba = models.FloatField()
    dga_subtype = models.CharField(max_length=250)
    dga_subtype_proba = models.FloatField()

# class Hosts(models.Model) :
#     ip = models.GenericIPAddressField(primary_key=True)
#     requests_count = models.IntegerField()