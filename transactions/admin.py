from django.contrib import admin
from .models import (
    SaleBill, 
    SaleItem,
    SaleBillDetails,
)

admin.site.register(SaleBill)
admin.site.register(SaleItem)
admin.site.register(SaleBillDetails)
