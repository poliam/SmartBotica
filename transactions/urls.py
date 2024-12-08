from django.urls import path
from . import views

urlpatterns = [
    # Sale URLs
    path('sales/', views.transaction_log, name='sales-list'),  # Add this line
    path('sales/new', views.SaleCreateView.as_view(), name='new-sale'),

    # AJAX functions for adding and clearing selected items in a sale
    path('add-to-selected-items/', views.add_to_selected_items, name='add-to-selected-items'),
    path('clear-selected-items/', views.clear_selected_items, name='clear-selected-items'),
    path('log/', views.transaction_log, name='transaction-log'),  # Define the route
    path('export-monthly-sales/', views.export_monthly_sales, name='export-monthly-sales'),

]
