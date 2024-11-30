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

def home_view(request):
    # Get the current time for greeting
    current_time = datetime.now().time()
    greeting = "Good morning" if current_time < time(12, 0) else "Good afternoon" if current_time < time(18, 0) else "Good evening"

    # Calculate the weekly sales data
    today = datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    dates = [start_of_week + timedelta(days=x) for x in range(7)]

    # Fetch weekly sales data and populate the dictionary for each date
    sales_data = SaleItem.objects.filter(billno__time__date__range=[start_of_week, end_of_week]).values('billno__time__date').annotate(total_sales=Sum('totalprice')).order_by('billno__time__date')
    sales_dict = {data['billno__time__date']: float(data['total_sales']) for data in sales_data}

    sales_labels = [date.strftime('%A') for date in dates]
    sales_values = [sales_dict.get(date, 0) for date in dates]
    sales_max = max(sales_values) if sales_values else 0

    # Calculate inventory status, revenue, medicine availability, and shortage
    total_revenue = SaleItem.objects.aggregate(total=Sum('totalprice')).get('total', 0) or 0
    medicines_available = Stock.objects.filter(is_deleted=False).count()
    medicine_shortage = Stock.objects.filter(quantity__lt=F('threshold'), is_deleted=False).count()

    # Define inventory status based on medicine shortage
    if medicine_shortage >= 5:
        inventory_status = "Warning"
    else:
        inventory_status = "Good"

    # Get products with low stock
    low_stock_products = Stock.objects.filter(quantity__lt=F('threshold'), is_deleted=False)

    # Top 3 products sold today
    # Top 3 products sold today
    top_products = SaleItem.objects.filter(
    billno__time__date=today  # Filters SaleItems for today's date
).values(
    'product__generic_name'  # Includes the product's generic name
).annotate(
    total_quantity=Sum('quantity')  # Sums the total quantity sold for each product
).order_by('-total_quantity')[:3]  # Orders by total quantity (desc) and limits to top 3



    context = {
        'greeting': greeting,
        'sales_data': sales_values,
        'sales_labels': sales_labels,
        'sales_max': sales_max,
        'low_stock_products': low_stock_products,
        'top_products': top_products,
        'overview_data': {
            'inventory_status': inventory_status,
            'revenue': total_revenue,
            'medicines_available': medicines_available,
            'medicine_shortage': medicine_shortage,
        }
    }
    return render(request, 'home.html', context)


def get_sales_data(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Convert start_date and end_date to datetime objects
    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

    # Generate a list of dates for the selected date range
    dates = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]

    sales_data = SaleItem.objects.filter(
        billno__time__date__range=[start_date, end_date]
    ).values('billno__time__date').annotate(total_sales=Sum('totalprice')).order_by('billno__time__date')

    # Create a dictionary to store sales data for each date
    sales_dict = {data['billno__time__date']: float(data['total_sales']) for data in sales_data}

    # Prepare data and labels for the line graph
    sales_labels = [date.strftime('%Y-%m-%d') for date in dates]
    sales_values = [sales_dict.get(date, 0) for date in dates]

    data = {
        'sales_labels': sales_labels,
        'sales_values': sales_values,
    }
    return JsonResponse(data)

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
