from django import forms
from .models import DosageForm
from .models import Stock, StockHistory, DosageForm, PharmacologicCategory
class StockForm(forms.ModelForm):
    item_no = forms.IntegerField(
        required=False, 
        widget=forms.NumberInput(attrs={'readonly': True, 'class': 'form-control'}),
        label="Item Number"
    )
    is_deleted = forms.BooleanField(
        required=False,
        label="Is Deleted",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    threshold = forms.IntegerField(
        required=False,
        label="Threshold (Minimum Stock Level)",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Stock
        fields = [
            'item_no',
            'generic_name',
            'brand_name',
            'dosage_strength',
            'form',
            'classification',
            'pharmacologic_category',
            'quantity',
            'expiry_date',
            'threshold',
            'is_deleted'
        ]
        labels = {
            'generic_name': 'Generic Name',
            'brand_name': 'Brand Name',
            'dosage_strength': 'Dosage Strength',
            'form': 'Form',
            'classification': 'Classification',
            'pharmacologic_category': 'Pharmacologic Category',
            'quantity': 'Quantity',
            'expiry_date': 'Expiry Date',
            'threshold': 'Threshold (Minimum Stock Level)',
            'is_deleted': 'Is Deleted'
        }
        widgets = {
            'generic_name': forms.TextInput(attrs={'class': 'form-control'}),
            'brand_name': forms.TextInput(attrs={'class': 'form-control'}),
            'dosage_strength': forms.TextInput(attrs={'class': 'form-control'}),
            'form': forms.Select(attrs={'class': 'form-control'}),
            'classification': forms.TextInput(attrs={'class': 'form-control'}),
            'pharmacologic_category': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

class AddStockForm(forms.ModelForm):
    quantity_added = forms.IntegerField(
        required=True,
        widget=forms.NumberInput(attrs={'min': 1}),
        label="Quantity to Add"
    )
    expiry_date = forms.DateField(  # Corrected field name to match the model
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Expiration Date"
    )

    class Meta:
        model = StockHistory
        fields = ['quantity_added', 'expiry_date']  # Use the correct field name

class AddMedicineForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = [
            'generic_name',
            'brand_name',
            'dosage_strength',
            'form',
            'classification',
            'pharmacologic_category',
            'expiry_date',
        ]
        widgets = {
            'form': forms.Select(attrs={'class': 'form-control'}),
            'pharmacologic_category': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['form'].queryset = DosageForm.objects.all()
        self.fields['pharmacologic_category'].queryset = PharmacologicCategory.objects.all()


from django import forms
from .models import DosageForm

class DosageFormEditForm(forms.ModelForm):
    class Meta:
        model = DosageForm
        fields = ['name']
        labels = {
            'name': 'Dosage Form Name',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }

from django import forms
from .models import PharmacologicCategory

class PharmacologicCategoryForm(forms.ModelForm):
    class Meta:
        model = PharmacologicCategory
        fields = ['name']
        labels = {
            'name': 'Pharmacologic Category Name',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }