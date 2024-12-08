from django.urls import path, re_path
from django.conf.urls import url
from . import views
from .views import (home_view, AboutView, get_sales_data, generate_sales_report, update_password,demand_predictions,data_analytics,)


urlpatterns = [
    path('', home_view, name='home'),
    path('about/', AboutView.as_view(), name='about'),
    path('get-sales-data/', get_sales_data, name='get_sales_data'),
    path('update-password/', views.update_password, name='update_password'),
    path('get-sales-data/', get_sales_data, name='get_sales_data'),
    path('generate-sales-report/', generate_sales_report, name='generate_sales_report'),
    path('demand-predictions/', demand_predictions, name='demand-predictions'),
    path('data-analytics/', data_analytics, name='data-analytics'),

    # Add other URL patterns here
]