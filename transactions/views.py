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
import datetime

logger = logging.getLogger(__name__)

@require_POST
def add_to_selected_items(request):
    try:
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))
        price = float(request.POST.get('price', 0.0))

        if not product_id or not quantity or price <= 0:
            return JsonResponse({'error': 'Product ID, quantity, and price are required.'}, status=400)

        product = get_object_or_404(Stock, pk=product_id)

        if product.quantity < quantity:
            return JsonResponse({'error': f'Not enough stock for {product.generic_name}.'}, status=400)

        product.quantity -= quantity
        product.save()

        selected_items = request.session.get('selected_items', [])
        selected_items.append({
            'product_id': product.pk,
            'product_name': f"{product.generic_name} ({product.brand_name})",
            'quantity': quantity,
            'price': str(price),
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
            selected_items_json = request.POST.get('selected_items', '[]')
            selected_items = json.loads(selected_items_json)

            if not selected_items:
                messages.error(request, "No items selected for sale.")
                return redirect('new-sale')

            sale_bill = SaleBill.objects.create(salesperson=request.user)

            for item in selected_items:
                try:
                    product = Stock.objects.get(item_no=item['product_id'])
                    quantity = int(item['quantity'])
                    manual_price = float(item['price'])

                    if manual_price <= 0 or quantity <= 0:
                        raise ValueError(f"Invalid data for {product.generic_name}")

                    stock_batches = product.history.filter(
                        quantity_added__gt=0,
                        expiry_date__gte=datetime.date.today()
                    ).order_by('expiry_date')

                    remaining_quantity = quantity

                    for batch in stock_batches:
                        if remaining_quantity <= 0:
                            break

                        deduct = min(batch.quantity_added, remaining_quantity)
                        batch.quantity_added -= deduct
                        remaining_quantity -= deduct
                        batch.save()

                    if remaining_quantity > 0:
                        logger.error(f"Partial stock deduction for {product.generic_name}. Requested: {quantity}, Available: {quantity - remaining_quantity}")
                        raise ValueError(f"Only {quantity - remaining_quantity} items were available for {product.generic_name}.")

                    product.quantity -= quantity
                    product.save()

                    SaleItem.objects.create(
                        billno=sale_bill,
                        product=product,
                        quantity=quantity,
                        perprice=manual_price,
                        totalprice=quantity * manual_price
                    )
                except Stock.DoesNotExist:
                    logger.error(f"Product with ID {item['product_id']} does not exist.")
                    messages.error(request, f"Product with ID {item['product_id']} does not exist.")
                    return redirect('new-sale')
                except Exception as e:
                    logger.error(f"Error processing product {item['product_id']}: {e}")
                    messages.error(request, f"Error processing product {item['product_id']}: {e}")
                    return redirect('new-sale')

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
    sale_bills = SaleBill.objects.prefetch_related('salebillno').all().order_by('-time')
    paginator = Paginator(sale_bills, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'sale_bills': page_obj.object_list,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
    }
    return render(request, 'sales/transaction_log.html', context)

import csv
from django.http import HttpResponse
from django.db.models import Max
from django.db.models import Sum

def export_monthly_sales(request):
    # Get the specific month and selected columns from the request
    month = request.GET.get('month')
    selected_columns = request.GET.getlist('columns')

    if not month:
        latest_sale = SaleBill.objects.aggregate(latest_time=Max('time'))
        if latest_sale['latest_time']:
            month = latest_sale['latest_time'].strftime('%Y-%m')  # Extract year and month
        else:
            response = HttpResponse(content_type='text/plain')
            response.write("No sales data available.")
            return response

    # Filter transactions for the specific or latest month
    sales = SaleBill.objects.prefetch_related('salebillno__product').filter(time__startswith=month).order_by('time')

    if not sales.exists():
        response = HttpResponse(content_type='text/plain')
        response.write(f"No sales records found for the month: {month}.")
        return response

    # Create the HTTP response for CSV download
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="sales_{month}.csv"'

    # Define column headers based on selected columns
    column_headers = {
        'sale_id': 'Sale ID',
        'date': 'Date',
        'total_amount': 'Total Amount',
        'handled_by': 'Handled By',
        'product_details': 'Product Details',
    }

    # Filter headers based on selected columns
    headers = [column_headers[col] for col in selected_columns]
    writer = csv.writer(response)
    writer.writerow(headers)  # Write the header row

    # Write rows based on selected columns
    for sale in sales:
        row = []
        if 'sale_id' in selected_columns:
            row.append(sale.pk)  # Sale ID
        if 'date' in selected_columns:
            row.append(sale.time.strftime('%Y-%m-%d %H:%M:%S'))  # Date
        if 'total_amount' in selected_columns:
            row.append(sale.get_total_price())  # Total Amount
        if 'handled_by' in selected_columns:
            row.append(sale.salesperson.username)  # Handled By
        if 'product_details' in selected_columns:
            product_details = " | ".join(
                f"{item.product.generic_name} ({item.product.brand_name}), Qty: {item.quantity}, Unit Price: {item.perprice}, Total: {item.totalprice}"
                for item in sale.salebillno.all()
            )
            row.append(product_details)  # Product Details
        writer.writerow(row)

    return response

