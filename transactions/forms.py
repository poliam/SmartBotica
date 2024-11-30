from django import forms
from .models import SaleBill, SaleItem, Stock

class SaleForm(forms.ModelForm):
    class Meta:
        model = SaleBill
        fields = []  # Remove 'discount_percentage' field


class SaleItemForm(forms.ModelForm):
    class Meta:
        model = SaleItem
        fields = ['product', 'quantity', 'perprice']  # Add 'perprice' for manual price input
        labels = {
            'product': 'Product',
            'quantity': 'Quantity',
            'perprice': 'Price per Unit',
        }
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'perprice': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
