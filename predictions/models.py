from django.db import models
import pmdarima as pm
import pandas as pd

# Create your models here.
class SalesData(models.Model):
    date = models.DateField()
    sales = models.FloatField()


