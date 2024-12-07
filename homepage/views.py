from django.shortcuts import render, redirect
from django.db.models import Sum, F
from django.utils import timezone
from transactions.models import SaleItem, SaleBill
from inventory.models import Stock
from datetime import datetime, timedelta, time
from django.http import JsonResponse, HttpResponse
from django.views.generic import TemplateView, View
import csv
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth import login
from .forms import UpdatePasswordForm
from datetime import datetime

def update_password(request):
    if request.method == 'POST':
        form = UpdatePasswordForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Your password has been updated successfully.')
            return redirect('login')
    else:
        form = UpdatePasswordForm()

    return render(request, 'update_password.html', {'form': form})

from datetime import timedelta

def home_view(request):
    filter_option = request.GET.get('filter', 'weekly')
    today = datetime.now().date()

    # Determine start and end dates based on the selected filter
    if filter_option == 'daily':
        start_date = today
        end_date = today
    elif filter_option == 'weekly':
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
    elif filter_option == 'monthly':
        start_date = today.replace(day=1)
        next_month = start_date.replace(day=28) + timedelta(days=4)
        end_date = next_month.replace(day=1) - timedelta(days=1)
    elif filter_option == 'yearly':
        start_date = today.replace(month=1, day=1)
        end_date = today.replace(month=12, day=31)
    elif filter_option == 'overall':  # New overall filter
        start_date, end_date = None, None
    else:
        start_date, end_date = None, None  # Default fallback for invalid filter

    # Fetch filtered sales data
    if start_date and end_date:
        sales_data = SaleItem.objects.filter(
            billno__time__date__range=[start_date, end_date]
        ).values('billno__time__date').annotate(total_sales=Sum('totalprice')).order_by('billno__time__date')
    else:  # Overall sales
        sales_data = SaleItem.objects.values('billno__time__date').annotate(total_sales=Sum('totalprice')).order_by('billno__time__date')

    # Fetch top products based on the filter
    if start_date and end_date:
        top_products = SaleItem.objects.filter(
            billno__time__date__range=[start_date, end_date]
        ).values(
            'product__generic_name'
        ).annotate(total_quantity=Sum('quantity')).order_by('-total_quantity')[:3]
    else:  # Overall top products
        top_products = SaleItem.objects.values(
            'product__generic_name'
        ).annotate(total_quantity=Sum('quantity')).order_by('-total_quantity')[:3]

    # Prepare data for the chart
    sales_dict = {data['billno__time__date']: float(data['total_sales']) for data in sales_data}
    if start_date and end_date:
        dates = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]
    else:
        dates = list(sales_dict.keys())  # Use existing dates for overall data
    sales_labels = [date.strftime('%Y-%m-%d') for date in dates]
    sales_values = [sales_dict.get(date, 0) for date in dates]
    sales_max = max(sales_values, default=100)

    # Other dashboard data
    total_revenue = SaleItem.objects.filter(
        billno__time__date__range=[start_date, end_date]
    ).aggregate(total=Sum('totalprice')).get('total', 0) or 0 if start_date and end_date else SaleItem.objects.aggregate(total=Sum('totalprice')).get('total', 0) or 0

    medicines_available = Stock.objects.filter(is_deleted=False).count()
    medicine_shortage = Stock.objects.filter(quantity__lt=F('threshold'), is_deleted=False).count()

    inventory_status = "Warning" if medicine_shortage >= 5 else "Good"

    # Fetch medicines nearing expiry (e.g., within the next 30 days)
    near_expiry_products = Stock.objects.filter(
        expiry_date__lte=today + timedelta(days=30),  # Expiring within 30 days
        expiry_date__gte=today,                      # Not expired yet
        is_deleted=False
    ).order_by('expiry_date')

    context = {
        'sales_data': sales_values,
        'sales_labels': sales_labels,
        'sales_max': sales_max,
        'overview_data': {
            'inventory_status': inventory_status,
            'revenue': total_revenue,
            'medicines_available': medicines_available,
            'medicine_shortage': medicine_shortage,
        },
        'near_expiry_products': near_expiry_products,  # Pass near-expiry products to the template
        'top_products': top_products,
        'selected_filter': filter_option,
    }
    return render(request, 'home.html', context)


from django.http import JsonResponse
from datetime import datetime, timedelta

def get_sales_data(request):
    filter_option = request.GET.get('filter', 'weekly')
    today = datetime.now().date()

    # Determine date range based on filter
    if filter_option == 'daily':
        start_date, end_date = today, today
    elif filter_option == 'weekly':
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
    elif filter_option == 'monthly':
        start_date = today.replace(day=1)
        end_date = (start_date + timedelta(days=31)).replace(day=1) - timedelta(days=1)
    elif filter_option == 'yearly':
        start_date = today.replace(month=1, day=1)
        end_date = today.replace(month=12, day=31)
    elif filter_option == 'overall':
        start_date, end_date = None, None  # Include all data
    else:
        return JsonResponse({'error': 'Invalid filter option'}, status=400)

    # Fetch sales data and total revenue
    if start_date and end_date:
        sales_data = SaleItem.objects.filter(
            billno__time__date__range=[start_date, end_date]
        ).values('billno__time__date').annotate(total_sales=Sum('totalprice')).order_by('billno__time__date')
        total_revenue = SaleItem.objects.filter(
            billno__time__date__range=[start_date, end_date]
        ).aggregate(total=Sum('totalprice'))['total'] or 0
        top_products = SaleItem.objects.filter(
            billno__time__date__range=[start_date, end_date]
        ).values('product__generic_name').annotate(
            total_quantity=Sum('quantity')
        ).order_by('-total_quantity')[:3]
    else:
        sales_data = SaleItem.objects.values('billno__time__date').annotate(
            total_sales=Sum('totalprice')
        ).order_by('billno__time__date')
        total_revenue = SaleItem.objects.aggregate(total=Sum('totalprice'))['total'] or 0
        top_products = SaleItem.objects.values(
            'product__generic_name'
        ).annotate(
            total_quantity=Sum('quantity')
        ).order_by('-total_quantity')[:3]

    # Prepare chart data
    sales_dict = {str(data['billno__time__date']): float(data['total_sales']) for data in sales_data}
    sales_labels = list(sales_dict.keys())
    sales_values = list(sales_dict.values())

    # Format top products
    formatted_top_products = [
        {'name': product['product__generic_name'], 'quantity': product['total_quantity']}
        for product in top_products
    ]

    return JsonResponse({
        'sales_labels': sales_labels,
        'sales_values': sales_values,
        'total_revenue': total_revenue,
        'top_products': formatted_top_products,
    })




@require_POST
def generate_sales_report(request):
    selected_date = request.POST.get('selected_date')
    sale_dates = SaleItem.objects.values_list('billno__time__date', flat=True).distinct()

    # Create a response object with CSV content type
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sales_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Product', 'Quantity Sold'])

    # Iterate over each sale date and generate report data
    for sale_date in sale_dates:
        products_sold = SaleItem.objects.filter(
            billno__time__date=sale_date
        ).values('product__product_name').annotate(total_quantity=Sum('quantity'))

        # Write the data rows for each product sold on the current date
        for product in products_sold:
            writer.writerow([sale_date, product['product__product_name'], product['total_quantity']])

    return response

class AboutView(TemplateView):
    template_name = "about.html"

def demand_predictions(request):
    # Logic for the Demand Predictions page
    context = {
        'title': 'Demand Predictions',
    }
    return render(request, 'demand_predictions.html', context)

def data_analytics(request):
    # Logic for the Data Analytics page
    context = {
        'title': 'Data Analytics',
    }
    return render(request, 'data_analytics.html', context)

