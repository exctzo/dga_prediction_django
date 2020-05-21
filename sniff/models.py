from django.db import models
from get_model.models import PreparedDataset, PreparedModel

class Request(models.Model) :
    ip_dst = models.GenericIPAddressField()
    ip_src = models.GenericIPAddressField()
    qname = models.CharField(max_length=250)
    report_date = models.DateTimeField(auto_now_add=True)
    dga = models.IntegerField()
    dga_proba = models.FloatField()
    dga_subtype = models.CharField(max_length=250,null=True)
    dga_subtype_proba = models.FloatField(null=True)
    id_dataset = models.ForeignKey(PreparedDataset, on_delete=models.SET_NULL, blank=True, null=True)
    id_model_dga = models.ForeignKey(PreparedModel, on_delete=models.SET_NULL, blank=True, null=True, related_name='id_model_dga')
    id_model_family = models.ForeignKey(PreparedModel, on_delete=models.SET_NULL, blank=True, null=True, related_name='id_model_family')