from django.db import models

class PreparedDataset(models.Model) :
    report_date = models.DateTimeField(auto_now_add=True)
    legit_size = models.IntegerField()
    dga_size = models.IntegerField()
    family_size = models.IntegerField()

class PreparedModel(models.Model) :
    report_date = models.DateTimeField(auto_now_add=True)
    model_type = models.CharField(max_length=20)
    model = models.CharField(max_length=20)
    id_dataset = models.ForeignKey('PreparedDataset')
    max_features = models.IntegerField()
    model_units = models.IntegerField()
    drop_rate = models.FloatField()
    classes = models.IntegerField()
    act_func = models.CharField(max_length=50)
    test_size = models.FloatField()
    epochs = models.IntegerField()
    batch_size = models.IntegerField()

class ModelLearningStat(models.Model) :
    report_date = models.DateTimeField(auto_now_add=True)
    id_model= models.ForeignKey('PreparedModel')
    epoch = models.IntegerField()
    auc = models.FloatField(blank=True, null=True)
    accuracy = models.FloatField()
    precision = models.FloatField()
    recall = models.FloatField()
    f1 = models.FloatField()