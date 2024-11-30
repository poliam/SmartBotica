from django.urls import path
from .views import populate_dosage_forms, edit_dosage_form, delete_dosage_form
from .forms import DosageFormEditForm
from .views import (
    populate_pharmacologic_categories,
    edit_pharmacologic_category,
    delete_pharmacologic_category,
    edit_medicine,
    add_new_stock_view
)
from .views import add_medicine, AddMedicineHistoryView
from . import views


urlpatterns = [
    # Inventory management
    path('', views.StockListView.as_view(), name='inventory'),
    path('new/', views.StockCreateView.as_view(), name='new-stock'),
    path('fetch-product-details/<int:product_id>/', views.fetch_product_details, name='fetch-product-details'),
    path('inventory/suggestions/', views.search_suggestions, name='inventory-suggestions'),
    path('inventory/add-medicine/', views.add_medicine, name='add-medicine'),
    path('add-new-stock/', add_new_stock_view, name='add-new-stock'),

    # Stock history views
    path('stock/<int:pk>/history/', views.ViewStockHistory.as_view(), name='view-stock-history'),

    # Stock out management
    path('stock/out/', views.StockOutView.as_view(), name='general-stock-out'),
    path('stock/out/confirm/', views.ConfirmStockOutView.as_view(), name='confirm-stock-out'),
    path('stock/<int:pk>/view-stock-out/', views.ViewStockOutHistory.as_view(), name='view-stock-out'),

    # Additional views
    path('fetch_dosage_forms/', views.fetch_dosage_forms, name='fetch_dosage_forms'),
    path('fetch_pharmacologic_categories/', views.fetch_pharmacologic_categories, name='fetch_pharmacologic_categories'),
    path('add-medicine-history/', views.AddMedicineHistoryView.as_view(), name='add-medicine-history'),
    path('populate-dosage-forms/', views.populate_dosage_forms, name='populate-dosage-forms'),
    path('populate-pharmacologic-categories/', views.populate_pharmacologic_categories, name='populate-pharmacologic-categories'),
    path('stock/suggestions/', views.stock_suggestions, name='stock-suggestions'),
    path('dosage-forms/', populate_dosage_forms, name='populate-dosage-forms'),
    path('dosage-forms/edit/<int:pk>/', edit_dosage_form, name='edit-dosage-form'),
    path('dosage-forms/delete/<int:pk>/', delete_dosage_form, name='delete-dosage-form'),
    path('pharmacologic-categories/', populate_pharmacologic_categories, name='populate-pharmacologic-categories'),
    path('pharmacologic-categories/edit/<int:pk>/', edit_pharmacologic_category, name='edit-pharmacologic-category'),
    path('pharmacologic-categories/delete/<int:pk>/', delete_pharmacologic_category, name='delete-pharmacologic-category'),
    path('add-medicine/', add_medicine, name='add-medicine'),
    path('add-medicine-history/', AddMedicineHistoryView.as_view(), name='add-medicine-history'),
    path('search-products/', views.search_suggestions, name='search-products'),
    path('edit-medicine/<int:pk>/', edit_medicine, name='edit-medicine'),

]
