from django.db import models

class Requests(models.Model) :
    ip_dst = models.GenericIPAddressField()
    ip_src = models.GenericIPAddressField()
    qname = models.CharField(max_length=250)
    report_date = models.DateTimeField(auto_now_add=True)
    dga = models.IntegerField()
    dga_proba = models.FloatField()
    dga_subtype = models.CharField(max_length=250,null=True)
    dga_subtype_proba = models.FloatField(null=True)