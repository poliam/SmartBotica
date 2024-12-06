from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from .models import SaleBill, SaleItem
from inventory.models import Stock
from .forms import SaleForm, SaleItemForm
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import logging
import json  # Ensure this line is added
from django.core.paginator import Paginator

logger = logging.getLogger(__name__)

@require_POST
def add_to_selected_items(request):
    try:
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))
        price = float(request.POST.get('price', 0.0))  # Fetch the price from the form

        if not product_id or not quantity or price <= 0:
            return JsonResponse({'error': 'Product ID, quantity, and price are required.'}, status=400)

        product = get_object_or_404(Stock, pk=product_id)

        if product.quantity < quantity:
            return JsonResponse({'error': f'Not enough stock for {product.generic_name}.'}, status=400)

        selected_items = request.session.get('selected_items', [])
        selected_items.append({
            'product_id': product.pk,
            'product_name': f"{product.generic_name} ({product.brand_name})",
            'quantity': quantity,
            'price': str(price),  # Use manually entered price
            'total': str(quantity * price)
        })
        request.session['selected_items'] = selected_items

        return JsonResponse({'message': 'Product added to list.'})
    except Exception as e:
        logger.error(f"Error in add_to_selected_items: {e}")
        return JsonResponse({'error': 'An error occurred while adding the item.'}, status=500)

def clear_selected_items(request):
    request.session.pop('selected_items', None)
    return JsonResponse({'message': 'Selected items cleared.'})

class SaleCreateView(View):
    template_name = 'sales/new_sale.html'

    def get(self, request):
        form = SaleForm()
        sale_item_form = SaleItemForm()
        selected_items = request.session.get('selected_items', [])
        logger.debug(f"Selected items on GET: {selected_items}")

        context = {
            'form': form,
            'sale_item_form': sale_item_form,
            'selected_items': selected_items,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        try:
            # Get the selected items from the hidden input field
            selected_items_json = request.POST.get('selected_items', '[]')
            selected_items = json.loads(selected_items_json)

            # Ensure there are items to process
            if not selected_items:
                messages.error(request, "No items selected for sale.")
                return redirect('new-sale')

            # Create a new SaleBill with the current user as the salesperson
            sale_bill = SaleBill.objects.create(salesperson=request.user)

            for item in selected_items:
                try:
                    product = Stock.objects.get(item_no=item['product_id'])
                    quantity = int(item['quantity'])
                    manual_price = float(item['price'])

                    if manual_price <= 0 or quantity <= 0:
                        raise ValueError(f"Invalid data for {product.generic_name}")

                    # Deduct stock from batches with the nearest expiry first
                    stock_batches = product.history.filter(quantity_added__gt=0).order_by('expiry_date')

                    for batch in stock_batches:
                        if quantity <= 0:
                            break  # All required quantity has been deducted
                        if batch.quantity_added >= quantity:
                            batch.quantity_added -= quantity
                            quantity = 0
                        else:
                            quantity -= batch.quantity_added
                            batch.quantity_added = 0
                        batch.save()

                    # If there is still some quantity left to deduct (impossible stock request)
                    if quantity > 0:
                        raise ValueError(f"Not enough stock available for {product.generic_name}")

                    # Reduce the total quantity in Stock
                    product.quantity -= int(item['quantity'])
                    product.save()

                    # Create SaleItem
                    SaleItem.objects.create(
                        billno=sale_bill,
                        product=product,
                        quantity=item['quantity'],
                        perprice=manual_price,
                        totalprice=item['quantity'] * manual_price
                    )
                except Stock.DoesNotExist:
                    logger.error(f"Product with ID {item['product_id']} does not exist.")
                    messages.error(request, f"Product with ID {item['product_id']} does not exist.")
                    return redirect('new-sale')
                except Exception as e:
                    logger.error(f"Error processing product {item['product_id']}: {e}")
                    messages.error(request, f"Error processing product {item['product_id']}: {e}")
                    return redirect('new-sale')

            # Clear session data
            request.session.pop('selected_items', None)
            messages.success(request, f"Sale completed successfully by {request.user.username}.")
            return redirect('sales-list')

        except json.JSONDecodeError:
            logger.error("Invalid JSON format in selected_items.")
            messages.error(request, "Invalid data format. Please try again.")
            return redirect('new-sale')
        except Exception as e:
            logger.error(f"Error completing sale: {e}")
            messages.error(request, "An error occurred while completing the sale.")
            return redirect('new-sale')


def transaction_log(request):
    # Fetch all SaleBill objects with related SaleItems preloaded
    sale_bills = SaleBill.objects.prefetch_related('salebillno').all().order_by('-time')  # Order by the most recent
    paginator = Paginator(sale_bills, 10)  # Display 10 bills per page
    page_number = request.GET.get('page', 1)  # Get the current page number from the query parameter
    page_obj = paginator.get_page(page_number)  # Get the page object for the current page

    # Context with paginated results and page details
    context = {
        'sale_bills': page_obj.object_list,  # Paginated sale bills for the current page
        'page_obj': page_obj,               # Page object for navigation
        'is_paginated': page_obj.has_other_pages(),  # Boolean to check if pagination is needed
    }
    return render(request, 'sales/transaction_log.html', context)

import csv
from django.http import HttpResponse
from django.db.models import Max
from django.db.models import Sum

def export_monthly_sales(request):
    # Get the specific month from the query parameter, if provided
    month = request.GET.get('month', None)

    if not month:
        # Determine the latest month from the data
        latest_sale = SaleBill.objects.aggregate(latest_time=Max('time'))
        if latest_sale['latest_time']:
            month = latest_sale['latest_time'].strftime('%Y-%m')  # Extract the year and month
        else:
            # If no sales data exists, return an error response
            response = HttpResponse(content_type='text/plain')
            response.write("No sales data available.")
            return response

    # Filter transactions for the specific or latest month
    sales = SaleBill.objects.filter(time__startswith=month).order_by('time')  # Filter by month
    
    if not sales.exists():
        # If no sales exist for the month, return an empty CSV
        response = HttpResponse(content_type='text/plain')
        response.write(f"No sales records found for the month: {month}.")
        return response

    # Create the HTTP response for CSV download
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="sales_{month}.csv"'

    # Write data to CSV
    writer = csv.writer(response)
    writer.writerow(['Month', 'Sale ID', 'Date', 'Total Amount', 'Handled By'])  # CSV header

    # Populate CSV rows with sales data
    for sale in sales:
        writer.writerow([
            sale.time.strftime('%Y-%m'),  # Month
            sale.pk,                      # Sale ID
            sale.time.strftime('%Y-%m-%d %H:%M:%S'),  # Date and time
            sale.get_total_price(),       # Total amount
            sale.salesperson.username     # Handled by
        ])

    return response

