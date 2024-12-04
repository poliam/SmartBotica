from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
   path('', views.predictionDashboard, name="predictionDashboard"),
   path('forecast/', views.arima_prediction_view, name='arima_prediction_view'),
  
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)