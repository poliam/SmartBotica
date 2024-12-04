from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, FileResponse
import pmdarima as pm
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from .models import SalesData
from .utils import fit_auto_arima_model, get_sales_data

# Create your views here.
def predictionDashboard(request):
	return render(request, 'prediction_base.html')


def arima_prediction_view(request):
	# Fetch historical sales data and fit the Auto ARIMA model
	sales_data = get_sales_data()
	model = fit_auto_arima_model()

	# Actual sales data
	forecast = model.predict(n_periods=60)
	
	return render(request, 'arima_prediction.html', {'model': model, "forcast": forecast})

