from datetime import datetime
import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View, CreateView, UpdateView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.utils import timezone
from django.db.models import Min, Q
from dateutil.parser import parse
from django.core.paginator import Paginator

from .models import Stock, StockHistory, DosageForm, PharmacologicCategory
from .forms import StockForm, AddStockForm, AddMedicineForm
from django_filters.views import FilterView
from .filters import StockFilter
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from django.db.models.functions import Abs
from django.db.models import F, Value
from .models import DosageForm
from inventory.forms import DosageFormEditForm
from .models import PharmacologicCategory
from .forms import PharmacologicCategoryForm


from inventory import models
def fetch_dosage_forms(request):
    dosage_forms = DosageForm.objects.all().values('id', 'name')
    return JsonResponse({'dosage_forms': list(dosage_forms)})

def fetch_pharmacologic_categories(request):
    pharmacologic_categories = PharmacologicCategory.objects.all().values('id', 'name')
    return JsonResponse({'pharmacologic_categories': list(pharmacologic_categories)})



from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

class ViewStockHistory(View):
    template_name = "view_stock_history.html"

    def get(self, request, pk):
        stock = get_object_or_404(Stock, pk=pk)

        # Fetch stock history, ordered by date (latest first)
        stock_history_queryset = StockHistory.objects.filter(stock=stock).order_by('-date')

        # Add pagination
        paginator = Paginator(stock_history_queryset, 10)  # 10 records per page
        page_number = request.GET.get('page', 1)
        try:
            stock_history = paginator.page(page_number)
        except PageNotAnInteger:
            stock_history = paginator.page(1)
        except EmptyPage:
            stock_history = paginator.page(paginator.num_pages)

        return render(request, self.template_name, {
            'stock': stock,
            'stock_history': stock_history,
            'page_obj': stock_history,  # Used for pagination controls
            'is_paginated': stock_history.has_other_pages(),  # Checks if pagination is needed
        })

class StockListView(FilterView):
    filterset_class = StockFilter
    template_name = 'inventory.html'
    paginate_by = 10

    def get_queryset(self):
        queryset = Stock.objects.filter(is_deleted=False)
        search_query = self.request.GET.get('search', '')  # Fetch the search query
        logging.debug(f"Search Query: {search_query}")  # Log for debugging
        
        if search_query:
            queryset = queryset.filter(
                Q(generic_name__icontains=search_query) |
                Q(brand_name__icontains=search_query) |
                Q(dosage_strength__icontains=search_query) |
                Q(form__name__icontains=search_query) |
                Q(pharmacologic_category__name__icontains=search_query)
            )
        logging.debug(f"Filtered Queryset Count: {queryset.count()}")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context




from django.urls import reverse

def fetch_product_details(request, product_id):
    try:
        stock = Stock.objects.get(item_no=product_id)  # Fetch stock using item_no
        data = {
            'generic_name': stock.generic_name,
            'brand_name': stock.brand_name,
            'dosage_strength': stock.dosage_strength,
            'form': stock.form.name if stock.form else None,  # Corrected to use `form`
            'quantity': stock.quantity,
            'expiry_date': stock.expiry_date.strftime('%Y-%m-%d') if stock.expiry_date else None,
        }
        return JsonResponse(data)
    except Stock.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)


from django.http import JsonResponse
from inventory.models import Stock
from django.db.models import Q

def search_suggestions(request):
    query = request.GET.get('q', '').strip()
    suggestions = []

    if query:
        matching_stocks = Stock.objects.filter(
            Q(generic_name__icontains=query) | Q(brand_name__icontains=query),
            is_deleted=False,  # Ensure stock is active
            quantity__gt=0     # Only include stocks with available quantity
        ).distinct()

        # Include `quantity` in the response
        suggestions = list(
            matching_stocks.values(
                'pk',           # Product ID
                'generic_name', # Generic Name
                'brand_name',   # Brand Name
                'dosage_strength',  # Dosage Strength
                'form__name',   # Form Name
                'quantity'      # Available Quantity
            )
        )

    return JsonResponse({'suggestions': suggestions})




def form_valid(self, form):
    stock = form.save(commit=False)
    quantity_added = form.cleaned_data['quantity']  # Ensure this is mapped correctly
    expiry_date = form.cleaned_data.get('expiry_date')  # Match the field name in the model

    # Update stock quantity and expiry date
    stock.quantity += quantity_added
    stock.expiry_date = expiry_date
    stock.save()

    # Add to Stock History
    StockHistory.objects.create(
        stock=stock,
        quantity_added=quantity_added,
        total_quantity=stock.quantity,
        updated_by=self.request.user,
        expiry_date=expiry_date
    )

    return redirect(reverse('view-stock-history', kwargs={'pk': stock.pk}))


class StockUpdateView(SuccessMessageMixin, UpdateView):
    model = Stock
    form_class = StockForm
    template_name = "edit_stock.html"
    success_url = '/inventory'
    success_message = "Stock has been updated successfully"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = 'Edit Stock'
        context["savebtn"] = 'Update Stock'
        context["delbtn"] = 'Delete Stock'
        return context
from django.db.models import Min, F
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib import messages
from .models import Stock, StockHistory
from django.utils import timezone

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from .models import Stock, StockHistory
from django.utils import timezone
from django.db.models import Q
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure the logger to output debug information
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Ensure the log level is set to DEBUG
class StockCreateView(SuccessMessageMixin, CreateView):
    model = Stock
    form_class = AddStockForm
    template_name = "new_stock.html"
    success_message = "Stock quantity has been updated successfully"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["products"] = Stock.objects.filter(is_deleted=False)  # Ensure only active stocks are included
        context["dosage_forms"] = DosageForm.objects.all()
        context["pharmacologic_categories"] = PharmacologicCategory.objects.all()

        return context
    def form_valid(self, form):
        try:
            # Retrieve form data
            quantity_added = form.cleaned_data['quantity_added']  # Matches AddStockForm
            expiry_date = form.cleaned_data.get('expiry_date')  # Corrected to match the form and model

            # Get the stock instance and save it
            stock_id = self.request.POST.get('product_id')  # Fetch stock_id from POST data
            stock = Stock.objects.get(item_no=stock_id)

            stock.quantity += quantity_added  # Update quantity
            stock.expiry_date = expiry_date  # Update expiry date if provided
            stock.save()  # Save the updated stock

            # Log the stock update
            logging.debug(f"Stock updated successfully: {stock}")

            # Create a StockHistory record
            StockHistory.objects.create(
                stock=stock,  # Reference the updated stock instance
                quantity_added=quantity_added,
                total_quantity=stock.quantity,  # Updated total quantity in Stock
                updated_by=self.request.user if self.request.user.is_authenticated else None,
                expiry_date=expiry_date,  # Use expiry_date for consistency
            )

            # Log the stock history creation
            logging.debug(f"StockHistory created for stock: {stock}")

            # Redirect to stock history view
            messages.success(self.request, "Stock updated successfully.")
            return redirect('view-stock-history', pk=stock.pk)

        except Exception as e:
            # Log error and return with an error message
            logging.error(f"Error while updating stock: {e}")
            messages.error(self.request, "An error occurred while updating the stock. Please try again.")
            return redirect('new-stock')        
        
from datetime import datetime
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.views import View

class StockOutView(View):
    template_name = "stock_out.html"

    def get(self, request):
        # Fetch only active stocks with non-zero quantities
        products_queryset = Stock.objects.filter(is_deleted=False, quantity__gt=0).annotate(
            nearest_expiry_date=Min('history__expiry_date', filter=Q(history__quantity_added__gt=0))
        )
        
        # Add pagination
        paginator = Paginator(products_queryset, 10)  # Show 10 products per page
        page_number = request.GET.get('page')
        products = paginator.get_page(page_number)

        return render(request, self.template_name, {'products': products})

    def post(self, request):
        selected_products = request.POST.getlist('selected_products')
        errors = []
        success = []

        if not selected_products:
            messages.error(request, "No products selected for stock out.")
            return redirect('general-stock-out')

        for product_data in selected_products:
            try:
                if '-' not in product_data:
                    errors.append(f"Invalid product data format: {product_data}. Expected 'item_no-expiry_date'.")
                    continue

                stock_id, expiry_date = product_data.split('-', 1)

                # Validate stock ID
                if not stock_id.isdigit():
                    errors.append(f"Invalid stock ID: {stock_id}. Must be numeric.")
                    continue

                stock_id = int(stock_id)

                # Parse expiry_date
                expiry_date = (
                    datetime.strptime(expiry_date, "%Y-%m-%d").date()
                    if expiry_date.strip().lower() != "n/a"
                    else None
                )

                # Fetch stock
                stock = get_object_or_404(Stock, item_no=stock_id)

                # Check for quantity in POST
                quantity_to_stock_out = request.POST.get(f'stock_out_quantity_{stock_id}')
                if not quantity_to_stock_out:
                    errors.append(f"Stock out quantity for {stock.generic_name} is missing.")
                    continue

                quantity_to_stock_out = int(quantity_to_stock_out)

                # Validate stock out quantity
                if quantity_to_stock_out <= 0:
                    errors.append(f"Stock out quantity for {stock.generic_name} must be greater than 0.")
                    continue

                if quantity_to_stock_out > stock.quantity:
                    errors.append(f"Stock out quantity for {stock.generic_name} exceeds available quantity ({stock.quantity}).")
                    continue

                # Update stock
                stock.quantity -= quantity_to_stock_out
                stock.save()

                # Log stock out in history
                StockHistory.objects.create(
                    stock=stock,
                    quantity_added=-quantity_to_stock_out,
                    total_quantity=stock.quantity,
                    updated_by=request.user if request.user.is_authenticated else None,
                    expiry_date=expiry_date,
                )

                success.append(f"Successfully processed stock out for {stock.generic_name}.")
            except Exception as e:
                errors.append(f"Error processing stock out for {product_data}: {str(e)}")

        # Add success and error messages
        if success:
            messages.success(request, " | ".join(success))
        if errors:
            messages.error(request, " | ".join(errors))

        return redirect('general-stock-out')



class GeneralStockOutView(View):
    template_name = "stock_out.html"

    def post(self, request):
        selected_products = request.POST.getlist('selected_products')
        errors = []
        success = []

        if not selected_products:
            messages.error(request, "No products selected for stock out.")
            return redirect('general-stock-out')

        for product_data in selected_products:
            try:
                # Split the product_data string into item_no and expiry_date
                if '-' not in product_data:
                    errors.append(f"Invalid product data format: {product_data}. Expected 'item_no-expiry_date'.")
                    continue

                stock_id, expiry_date = product_data.split('-', 1)

                # Validate stock_id
                if not stock_id.isdigit():
                    errors.append(f"Invalid stock ID: {stock_id}. Must be numeric.")
                    continue

                stock_id = int(stock_id)

                # Validate and format expiry_date
                if expiry_date.strip().lower() != "n/a":
                    try:
                        # Parse and reformat expiry_date to "YYYY-MM-DD"
                        expiry_date_obj = datetime.strptime(expiry_date, "%Y-%m-%d")
                        expiry_date = expiry_date_obj.strftime("%Y-%m-%d")
                    except ValueError:
                        errors.append(f"Invalid expiry date format for product ID {stock_id}: {expiry_date}.")
                        continue
                else:
                    expiry_date = None

                # Fetch the stock item is missing.
                stock = get_object_or_404(Stock, item_no=stock_id)

                # Fetch the quantity to stock out
                quantity_to_stock_out = int(request.POST.get(f'stock_out_quantity_{stock_id}', 0))

                # Validation: Ensure sufficient stock
                if quantity_to_stock_out <= 0 or quantity_to_stock_out > stock.quantity:
                    errors.append(f"Invalid stock out quantity for {stock.generic_name}.")
                    continue

                # Reduce the stock quantity
                stock.quantity -= quantity_to_stock_out
                stock.save()

                # Log the stock out in StockHistory
                StockHistory.objects.create(
                    stock=stock,
                    quantity_added=-quantity_to_stock_out,
                    total_quantity=stock.quantity,
                    updated_by=request.user if request.user.is_authenticated else None,
                    expiry_date=expiry_date,
                )

                success.append(f"Successfully processed stock out for {stock.generic_name}.")
            except Exception as e:
                errors.append(f"Error processing stock out for {product_data}: {str(e)}")

        # Add messages for success and errors
        if success:
            messages.success(request, " | ".join(success))
        if errors:
            messages.error(request, " | ".join(errors))

        return redirect('general-stock-out')


from django.db import transaction

class ConfirmStockOutView(View):
    def post(self, request):
        selected_products = request.POST.getlist('selected_products')
        if not selected_products:
            messages.error(request, "No products selected for stock out.")
            return redirect('stock-out')

        errors = []
        success_messages = []

        try:
            with transaction.atomic():
                for item in selected_products:
                    try:
                        stock_id, expiry_date = item.split('-')
                        stock = Stock.objects.get(id=stock_id)

                        stock_out_quantity = int(request.POST.get(f'stock_out_quantity_{stock_id}', 0))
                        if stock_out_quantity <= 0:
                            errors.append(f"Invalid quantity for product: {stock.generic_name}.")
                            continue

                        # Validate stock availability for the specific expiry date
                        stock_history = StockHistory.objects.filter(
                            stock=stock,
                            expiry_date=expiry_date,
                            total_quantity__gte=stock_out_quantity
                        ).first()

                        if not stock_history:
                            errors.append(f"Not enough stock available for product: {stock.generic_name}.")
                            continue

                        # Deduct quantity from stock
                        stock.quantity -= stock_out_quantity
                        stock.save()

                        # Create a new stock history entry
                        StockHistory.objects.create(
                            stock=stock,
                            quantity_added=-stock_out_quantity,
                            total_quantity=stock.quantity,
                            updated_by=request.user,
                            expiry_date=expiry_date,
                            date=timezone.now()
                        )

                        success_messages.append(f"Stock out successful for product: {stock.generic_name}.")

                    except Exception as e:
                        errors.append(f"Error processing product ID {item}: {str(e)}")

        except Exception as e:
            errors.append(f"Critical error occurred: {str(e)}. Transaction rolled back.")

        # Display messages
        if errors:
            messages.error(request, " | ".join(errors))
        if success_messages:
            messages.success(request, " | ".join(success_messages))

        return redirect('stock-out')

def search_suggestions(request):
    query = request.GET.get('q', '').strip()
    suggestions = []

    if query:
        matching_stocks = Stock.objects.filter(
            Q(generic_name__icontains=query) | Q(brand_name__icontains=query),
            is_deleted=False,  # Ensure stock is active
            quantity__gt=0     # Only include stocks with available quantity
        ).distinct().values(
            'pk',
            'generic_name',
            'brand_name',
            'dosage_strength',
            'form__name',
            'quantity'  # Include quantity in response
        )
        suggestions = list(matching_stocks)

    # Log the response for debugging
    logging.debug(f"Suggestions sent: {suggestions}")
    return JsonResponse({'suggestions': suggestions})

def edit_medicine(request, pk):
    medicine = get_object_or_404(Stock, pk=pk)
    if request.method == "POST":
        form = StockForm(request.POST, instance=medicine)
        if form.is_valid():
            form.save()
            messages.success(request, "Medicine updated successfully.")
            return redirect('add-medicine-history')
    else:
        form = StockForm(instance=medicine)
    return render(request, 'edit_medicine.html', {'form': form})
def add_new_stock_view(request):
    low_stock_products = list(Stock.objects.filter(quantity__lt=F('threshold'), is_deleted=False))

    # Debugging the data passed to the template
    print("Low Stock Products in View:")
    for product in low_stock_products:
        print(f"Product: {product.generic_name}, Quantity: {product.quantity}, Threshold: {product.threshold}")

    context = {
        'low_stock_products': low_stock_products,  # Convert to list to avoid lazy evaluation issues
        'form': AddStockForm(),
    }
    return render(request, 'add_new_stock.html', context)



def add_medicine(request):
    if request.method == 'POST':
        form = AddMedicineForm(request.POST)
        if form.is_valid():
            # Extract form data
            generic_name = form.cleaned_data['generic_name']
            brand_name = form.cleaned_data['brand_name']
            dosage_strength = form.cleaned_data['dosage_strength']
            dosage_form_id = request.POST.get('form')
            pharmacologic_category_id = request.POST.get('pharmacologic_category')
            classification = form.cleaned_data['classification']

            # Check if a product with the same attributes already exists
            if Stock.objects.filter(
                generic_name=generic_name,
                brand_name=brand_name,
                dosage_strength=dosage_strength,
                form_id=dosage_form_id,
                classification=classification,
                pharmacologic_category_id=pharmacologic_category_id,
                is_deleted=False,
            ).exists():
                # Ensure only one error message is added
                if not any(message.message == "A product with the same details already exists. Please check the inventory." for message in messages.get_messages(request)):
                    messages.error(request, "A product with the same details already exists. Please check the inventory.")
                return redirect('add-medicine')

            try:
                # Validate and set the 'form' field
                form_instance = DosageForm.objects.get(id=dosage_form_id)

                # Validate and set the 'pharmacologic_category' field
                category_instance = PharmacologicCategory.objects.get(id=pharmacologic_category_id)

                # Save the medicine
                medicine = form.save(commit=False)
                medicine.form = form_instance
                medicine.pharmacologic_category = category_instance
                medicine.save()

                messages.success(request, "Medicine added successfully.")
                return redirect('add-medicine-history')

            except DosageForm.DoesNotExist:
                messages.error(request, "Selected Dosage Form does not exist.")
            except PharmacologicCategory.DoesNotExist:
                messages.error(request, "Selected Pharmacologic Category does not exist.")
            except Exception as e:
                messages.error(request, "An unexpected error occurred. Please try again.")
        else:
            # Form validation failed
            messages.error(request, "There was an error with the form submission. Please check your input.")
    else:
        form = AddMedicineForm()

    # Fetch dosage forms and pharmacologic categories for dropdowns
    context = {
        'form': form,
        'dosage_forms': DosageForm.objects.all(),
        'pharmacologic_categories': PharmacologicCategory.objects.all(),
    }
    return render(request, 'add_medicine.html', context)


class GeneralStockOutView(View):
    template_name = "stock_out.html"

    def get(self, request):
        # Fetch pharmacologic categories
        pharmacologic_categories = PharmacologicCategory.objects.all()

        # Fetch stock products with annotations
        products = Stock.objects.filter(is_deleted=False, quantity__gt=0).select_related('form', 'pharmacologic_category').annotate(
            nearest_expiry_date=Min(
                'history__expiry_date', filter=Q(history__quantity_added__gt=0)
            )
        )

        return render(request, self.template_name, {
            'pharmacologic_categories': pharmacologic_categories,
            'products': products,
            'search_query': request.GET.get('search', ''),
            'selected_category': request.GET.get('category', ''),
            'expiring_soon_checked': request.GET.get('expiring_soon', ''),
        })


    def post(self, request):
        selected_products = request.POST.getlist('selected_products')
        errors = []
        success = []

        if not selected_products:
            messages.error(request, "No products selected for stock out.")
            return redirect('general-stock-out')

        for product_data in selected_products:
            try:
                # Extract stock ID and expiry date
                stock_id, expiry_date = product_data.split('-')
                expiry_date = (
                    datetime.strptime(expiry_date, "%Y-%m-%d").date()
                    if expiry_date != "N/A"
                    else None
                )

                # Fetch the quantity to stock out
                quantity_to_stock_out = int(request.POST.get(f'stock_out_quantity_{stock_id}', 0))
                stock = get_object_or_404(Stock, pk=stock_id)

                # Validation: Ensure sufficient stock
                if quantity_to_stock_out <= 0 or quantity_to_stock_out > stock.quantity:
                    errors.append(f"Invalid stock out quantity for {stock.generic_name}.")
                    continue

                # Reduce the stock quantity
                stock.quantity -= quantity_to_stock_out
                stock.save()

                # Log the stock out in StockHistory
                StockHistory.objects.create(
                    stock=stock,
                    quantity_added=-quantity_to_stock_out,
                    total_quantity=stock.quantity,
                    updated_by=request.user if request.user.is_authenticated else None,
                    expiry_date=expiry_date,
                )

                success.append(f"Successfully processed stock out for {stock.generic_name}.")
            except Exception as e:
                errors.append(f"Error processing stock out: {e}")

        # Add messages to display on the page
        if success:
            messages.success(request, " | ".join(success))
        if errors:
            messages.error(request, " | ".join(errors))

        return redirect('general-stock-out')
def stock_suggestions(request):
    query = request.GET.get('q', '')
    suggestions = []

    if query:
        matching_stocks = Stock.objects.filter(
            Q(generic_name__icontains=query) |
            Q(brand_name__icontains=query) |
            Q(dosage_strength__icontains=query) |
            Q(form__name__icontains=query) |
            Q(pharmacologic_category__name__icontains=query)
        ).distinct()

        suggestions = list(
            matching_stocks.values(
                'pk',
                'generic_name',
                'brand_name',
                'dosage_strength',
                'form__name',
            )
        )

    return JsonResponse({'suggestions': suggestions})
from django.db.models import F


class ViewStockOutHistory(View):
    template_name = "view_stock_out.html"

    def get(self, request, pk):
        stock = get_object_or_404(Stock, pk=pk)
        # Annotate with the absolute value of quantity_added for display
        stock_out_history = StockHistory.objects.filter(    
            stock=stock, quantity_added__lt=0
        ).annotate(quantity_removed=Abs(F('quantity_added'))).order_by('-date')

        return render(request, self.template_name, {
            'stock': stock,
            'stock_out_history': stock_out_history,
        })
    
from django.views.generic import ListView

class AddMedicineHistoryView(ListView):
    model = Stock
    template_name = 'add_medicine_history.html'
    context_object_name = 'medicines'
    paginate_by = 10

    def get_queryset(self):
        return Stock.objects.filter(is_deleted=False).order_by('-last_updated')

def populate_dosage_forms(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            DosageForm.objects.create(name=name)
            messages.success(request, f"'{name}' added to Dosage Forms.")
            return redirect('populate-dosage-forms')
        messages.error(request, "Name cannot be empty.")

    dosage_forms = DosageForm.objects.all()
    return render(request, 'populate_dosage_forms.html', {'dosage_forms': dosage_forms})

# Edit Dosage Form
def edit_dosage_form(request, pk):
    dosage_form = get_object_or_404(DosageForm, pk=pk)
    if request.method == 'POST':
        form = DosageFormEditForm(request.POST, instance=dosage_form)
        if form.is_valid():
            form.save()
            messages.success(request, f"'{dosage_form.name}' updated successfully.")
            return redirect('populate-dosage-forms')
    else:
        form = DosageFormEditForm(instance=dosage_form)
    return render(request, 'edit_dosage_form.html', {'form': form, 'dosage_form': dosage_form})


# Delete Dosage Form
def delete_dosage_form(request, pk):
    dosage_form = get_object_or_404(DosageForm, pk=pk)
    if request.method == 'POST':
        dosage_form.delete()
        messages.success(request, f"'{dosage_form.name}' deleted successfully.")
        return redirect('populate-dosage-forms')
    return render(request, 'delete_dosage_form.html', {'dosage_form': dosage_form})


def populate_pharmacologic_categories(request):
    if request.method == 'POST':
        form = PharmacologicCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"'{form.cleaned_data['name']}' added successfully.")
            return redirect('populate-pharmacologic-categories')
        else:
            messages.error(request, "Error adding the category. Please try again.")

    pharmacologic_categories = PharmacologicCategory.objects.all()
    return render(request, 'populate_pharmacologic_categories.html', {
        'pharmacologic_categories': pharmacologic_categories,
    })

def edit_pharmacologic_category(request, pk):
    category = get_object_or_404(PharmacologicCategory, pk=pk)
    if request.method == 'POST':
        form = PharmacologicCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f"'{category.name}' updated successfully.")
            return redirect('populate-pharmacologic-categories')
    else:
        form = PharmacologicCategoryForm(instance=category)
    return render(request, 'edit_pharmacologic_category.html', {'form': form, 'category': category})

# Delete Pharmacologic Category
def delete_pharmacologic_category(request, pk):
    category = get_object_or_404(PharmacologicCategory, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, f"'{category.name}' deleted successfully.")
        return redirect('populate-pharmacologic-categories')
    return render(request, 'delete_pharmacologic_category.html', {'category': category})


def edit_medicine(request, pk):
    medicine = get_object_or_404(Stock, pk=pk)
    if request.method == 'POST':
        form = StockForm(request.POST, instance=medicine)
        # Exclude 'quantity' in this context
        form.fields.pop('quantity', None)
        if form.is_valid():
            form.save()
            messages.success(request, f"'{medicine.generic_name}' updated successfully.")
            return redirect('add-medicine-history')
        else:
            print("Form errors:", form.errors)
            messages.error(request, "Please correct the errors below.")
    else:
        form = StockForm(instance=medicine)
        # Exclude 'quantity' in this context
        form.fields.pop('quantity', None)
    return render(request, 'edit_medicine.html', {'form': form, 'medicine': medicine})



def delete_medicine(request, pk):
    medicine = get_object_or_404(Stock, pk=pk)
    if request.method == 'POST':
        medicine.delete()
        messages.success(request, f"'{medicine.generic_name}' deleted successfully.")
        return redirect('add-medicine-history')
    return render(request, 'delete_medicine.html', {'medicine': medicine})