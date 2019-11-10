from django.db import models

class Requests(models.Model) :
    ip_dst = models.GenericIPAddressField()
    ip_src = models.GenericIPAddressField()
    qname = models.CharField(max_length=250)
    report_date = models.DateField()
    dga = models.IntegerField()

# class Hosts(models.Model) :
#     ip = models.GenericIPAddressField(primary_key=True)
#     requests_count = models.IntegerField()