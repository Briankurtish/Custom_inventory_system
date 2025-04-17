from django.views.generic import TemplateView
from web_project import TemplateLayout
from .forms import BeginningInventoryForm, StockAddForm, StockUpdateForm, UpdateStockForm
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from apps.products.models import Batch, Product
from apps.branches.models import Branch
from .models import Stock, InventoryTransaction
from django.utils.timezone import now  # To handle timestamps
from django.http import JsonResponse
from apps.workers.models import Worker
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import authenticate
import json
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.http import Http404
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt




"""
This file is a view controller for multiple pages as a module.
Here you can override the page view layout.
Refer to tables/urls.py file for more pages.
"""

# Temp storage for demonstration; use sessions or database in production
TEMP_STOCK_LIST = []
TEMP_UPDATE_LIST = []  # Temporary list for selected stocks

@login_required
def ManageStockView(request):
    stocks = Stock.objects.all().order_by("product__generic_name__brand_name")


    paginator = Paginator(stocks, 100)
    page_number = request.GET.get('page')  # Get the current page number from the request
    paginated_stocks = paginator.get_page(page_number)

    offset = (paginated_stocks.number - 1) * paginator.per_page

    # Create a new context dictionary for this view
    view_context = {
        "stocks": paginated_stocks,
        "offset": offset,
    }

    # Initialize the template layout and merge the view context
    context = TemplateLayout.init(request, view_context)

    return render(request, 'stock.html', context)


@login_required
def ManageBranchStockView(request):
    # Get the branch associated with the logged-in worker
    user_branch = request.user.worker_profile.branch

    if not user_branch:
        raise Http404("You are not affiliated with any branch.")  # Handle unaffiliated workers gracefully

    # Get the search query and status filter from the request
    search_query = request.GET.get('search_query', '').strip()
    status_filter = request.GET.get('status_filter', '').strip()

    # Filter stocks by the user's branch
    stocks = Stock.objects.filter(branch=user_branch)

    # Apply search filter if search query is present
    if search_query:
        stocks = stocks.filter(
            Q(product__product_code__icontains=search_query) |
            Q(product__generic_name_dosage__generic_name__icontains=search_query) |
            Q(product__brand_name__brand_name__icontains=search_query) |
            Q(product__batch__batch_number__icontains=search_query)
        )

    # Apply status filter if selected
    if status_filter:
        if status_filter == 'in_stock':
            stocks = stocks.filter(total_stock__gt=200)  # In Stock
        elif status_filter == 'low_stock':
            stocks = stocks.filter(total_stock__lte=199)  # Low Stock (example: quantity <= 5)
        elif status_filter == 'out_of_stock':
            stocks = stocks.filter(total_stock=0)  # Out of Stock

    # Paginate the filtered stocks
    paginator = Paginator(stocks, 100)
    page_number = request.GET.get('page')  # Get the current page number from the request
    paginated_stocks = paginator.get_page(page_number)

    # Calculate offset for the current page
    offset = (paginated_stocks.number - 1) * paginator.per_page

    # Create a context dictionary with paginated stocks and offset
    view_context = {
        "stocks": paginated_stocks,
        "offset": offset,
        "user_branch_name": user_branch.branch_name,  # Pass branch name to display in the template
        "search_query": search_query,  # Include the search query in the context
        "status_filter": status_filter,  # Include the status filter in the context
    }

    # Initialize the template layout and merge the view context
    context = TemplateLayout.init(request, view_context)

    return render(request, 'stock_branch.html', context)


@login_required
def ManageStockBranchView(request):
    try:
        # Get the branch of the logged-in user from the Worker table
        worker = Worker.objects.select_related('branch').get(user=request.user)
        user_branch = worker.branch  # Get the branch instance
    except Worker.DoesNotExist:
        # Handle case where Worker profile does not exist
        user_branch = None

    if user_branch:
        # Filter stocks for the user's branch
        stocks = Stock.objects.filter(branch=user_branch)
    else:
        # No branch affiliated, show no stocks
        stocks = []

    # Create the context with filtered stocks
    view_context = {
        "stocks": stocks,
        "user_branch_name": user_branch.branch_name if user_branch else None,
    }

    # Merge the context with the template layout
    context = TemplateLayout.init(request, view_context)

    return render(request, 'stock_branch.html', context)



@login_required
def StockAuditLogView(request):
    logs = InventoryTransaction.objects.all().order_by('-transaction_date')
    paginator = Paginator(logs, 100)  # Paginate logs with 10 logs per page
    page_number = request.GET.get("page")  # Get the current page number from the request
    paginated_logs = paginator.get_page(page_number)  # Get the page object
    offset = (paginated_logs.number - 1) * paginator.per_page
    # Create a context dictionary for the view
    view_context = {
        "logs": paginated_logs,
        "offset": offset,
    }

    # Initialize the template layout and merge the view context
    context = TemplateLayout.init(request, view_context)

    return render(request, "stock_logs.html", context)


@login_required
def add_stock_view(request):
    form = StockAddForm()

    # Retrieve temporary stock list from session or create an empty list
    temp_stock_list = request.session.get("TEMP_STOCK_LIST", [])

    if request.method == "POST":
        if "add_to_list" in request.POST:  # Handle adding to the temporary list
            form = StockAddForm(request.POST)
            if form.is_valid():
                product = form.cleaned_data["product"]
                quantity = form.cleaned_data["quantity"]
                branch = form.cleaned_data["branch"]
                batch = form.cleaned_data["batch"]  # Get batch from form
                batch_number = batch.batch_number if batch else None

                # Check if the same product, branch, and batch already exists in the temp list
                existing_item = next(
                    (item for item in temp_stock_list
                     if item["product_code"] == product.product_code
                     and item["branch_id"] == branch.id
                     and item["batch_number"] == batch_number),
                    None
                )

                if existing_item:
                    # If the same product, branch, and batch exists, update the quantity
                    existing_item["quantity"] += quantity
                    messages.success(request, _("Quantity updated for existing item in the temporary stock list."))
                else:
                    # Add a new entry with batch info
                    temp_stock_list.append({
                        "product_code": product.product_code,
                        "product_name": str(product.generic_name_dosage),
                        "brand_name": str(product.brand_name.brand_name if product.brand_name else "No Brand"),
                        "quantity": quantity,
                        "branch_id": branch.id,
                        "branch_name": branch.branch_name,
                        "batch_number": batch_number,
                    })
                    messages.success(request, _("Item added to temporary stock list."))

                # Store the updated temporary list in session
                request.session["TEMP_STOCK_LIST"] = temp_stock_list
            else:
                messages.error(request, _("Invalid data. Please check the form."))

        elif "remove_item" in request.POST:  # Handle removing from the temporary list
            product_code = request.POST.get("product_code")
            branch_id = request.POST.get("branch")
            batch_number = request.POST.get("batch_number")

            # Remove matching item from the temporary list by product, branch, and batch
            temp_stock_list = [
                item for item in temp_stock_list
                if not (
                    item["product_code"] == product_code
                    and item["branch_id"] == int(branch_id)
                    and item["batch_number"] == batch_number
                )
            ]
            # Store the updated list in session
            request.session["TEMP_STOCK_LIST"] = temp_stock_list
            messages.success(request, _("Item removed from the temporary stock list."))

        elif "update_stock" in request.POST:  # Handle updating stock in the database
            for item in temp_stock_list:
                # Fetch Product and Batch
                product = Product.objects.get(
                        product_code=item["product_code"],
                        batch__batch_number=item["batch_number"]
                    )
                batch = Batch.objects.get(batch_number=item["batch_number"]) if item["batch_number"] else None
                branch = Branch.objects.get(id=item["branch_id"])

                # Update or create stock entry with batch
                stock, created = Stock.objects.update_or_create(
                    product=product,
                    branch=branch,
                    batch=batch,  # Include batch in the lookup
                    defaults={
                        "quantity": item["quantity"],
                        "created_by": request.user.worker_profile
                    }
                )

                # Create a transaction record
                transaction_type = 'add' if created else 'update'
                InventoryTransaction.objects.create(
                    product=product,
                    branch=branch,
                    quantity=item["quantity"],
                    transaction_type=transaction_type,
                    transaction_date=now(),
                    worker=request.user.worker_profile
                )

                if created:
                    messages.info(request, f"Stock added for product {product.generic_name_dosage} (Batch: {item['batch_number']}).")
                else:
                    messages.info(request, f"Stock updated for product {product.generic_name_dosage} (Batch: {item['batch_number']}).")

            # Clear the temporary list
            del request.session["TEMP_STOCK_LIST"]
            messages.success(request, _("Stock updated successfully."))
            return redirect("stock")  # Replace with the correct URL name

    # Prepare context for rendering
    view_context = {
        "form": form,
        "temp_stock": temp_stock_list,
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'AddStock.html', context)



# @login_required
# def add_stock_view(request):
#     form = StockAddForm()

#     # Retrieve temporary stock list from session or create an empty list
#     temp_stock_list = request.session.get("TEMP_STOCK_LIST", [])

#     if request.method == "POST":
#         if "add_to_list" in request.POST:  # Handle adding to the temporary list
#             form = StockAddForm(request.POST)
#             if form.is_valid():
#                 product = form.cleaned_data["product"]
#                 quantity = form.cleaned_data["quantity"]
#                 branch = form.cleaned_data["branch"]
#                 batch_number = product.batch.batch_number if product.batch else None  # Get batch number

#                 # Check if the same product (with same batch number and branch) already exists
#                 existing_item = next(
#                     (item for item in temp_stock_list
#                     if item["product_code"] == product.product_code
#                     and item["branch_id"] == branch.id
#                     and item["batch_number"] == batch_number),  # Ensure batch number is checked
#                     None
#                 )

#                 if existing_item:
#                     # If the same product with the same batch and branch exists, update the quantity
#                     existing_item["quantity"] += quantity
#                     messages.success(request, _("Quantity updated for existing item in the temporary stock list."))
#                 else:
#                     # If it's a new batch or branch, add as a new entry
#                     temp_stock_list.append({
#                         "product_code": product.product_code,
#                         "product_name": str(product.generic_name_dosage),
#                         "brand_name": str(product.brand_name.brand_name),
#                         "quantity": quantity,
#                         "branch_id": branch.id,
#                         "branch_name": branch.branch_name,
#                         "batch_number": batch_number,  # Add batch number to the temporary list
#                     })
#                     messages.success(request, _("Item added to temporary stock list."))

#                 # Store the updated temporary list in session
#                 request.session["TEMP_STOCK_LIST"] = temp_stock_list
#             else:
#                 messages.error(request, _("Invalid data. Please check the form."))

#         elif "remove_item" in request.POST:  # Handle removing from the temporary list
#             product_code = request.POST.get("product_code")
#             branch_id = request.POST.get("branch")
#             batch_number = request.POST.get("batch_number")

#             # Remove matching item from the temporary list
#             temp_stock_list = [
#                 item for item in temp_stock_list
#                 if not (
#                     item["product_code"] == product_code
#                     and item["branch_id"] == int(branch_id)
#                     and item["batch_number"] == batch_number
#                 )
#             ]
#             # Store the updated list in session
#             request.session["TEMP_STOCK_LIST"] = temp_stock_list
#             messages.success(request, _("Item removed from the temporary stock list."))

#         elif "update_stock" in request.POST:  # Handle updating stock in the database
#             for item in temp_stock_list:
#                 # Filter Product based on both product_code and batch_number
#                 product = Product.objects.get(
#                     product_code=item["product_code"],
#                     batch__batch_number=item["batch_number"]  # Match batch number
#                 )
#                 branch = Branch.objects.get(id=item["branch_id"])

#                 # Update or create stock entry
#                 stock, created = Stock.objects.update_or_create(
#                     product=product,
#                     branch=branch,
#                     defaults={
#                         "quantity": item["quantity"],
#                         "created_by": request.user.worker_profile  # Set the created_by field
#                     }
#                 )

#                 # Create a transaction record
#                 transaction_type = 'add' if created else 'update'
#                 InventoryTransaction.objects.create(
#                     product=product,
#                     branch=branch,
#                     quantity=item["quantity"],
#                     transaction_type=transaction_type,
#                     transaction_date=now(),
#                     worker=request.user.worker_profile  # Ensure worker tracking is included
#                 )

#                 if created:
#                     messages.info(request, f"Stock added for product {product.generic_name_dosage}.")
#                 else:
#                     messages.info(request, f"Stock updated for product {product.generic_name_dosage}.")

#             # Clear the temporary list
#             del request.session["TEMP_STOCK_LIST"]
#             messages.success(request, _("Stock updated successfully."))
#             return redirect("stock")  # Replace with the correct URL name

#     # Prepare context for rendering
#     view_context = {
#         "form": form,
#         "temp_stock": temp_stock_list,
#     }
#     context = TemplateLayout.init(request, view_context)

#     return render(request, 'AddStock.html', context)


@login_required
def add_beginning_inventory_view(request):
    form = BeginningInventoryForm()
    temp_beginning_inventory_list = request.session.get("TEMP_BEGINNING_INVENTORY_LIST", [])

    if request.method == "POST":
        if "add_to_list" in request.POST:
            form = BeginningInventoryForm(request.POST)
            if form.is_valid():
                product = form.cleaned_data["product"]
                branch = form.cleaned_data["branch"]
                fixed_beginning_inventory = form.cleaned_data["fixed_beginning_inventory"]
                batch_number = product.batch.batch_number if product.batch else None

                # Check if stock exists at this branch
                stock = Stock.objects.filter(product=product, branch=branch).first()

                if stock and stock.fixed_beginning_inventory > 0:
                    messages.warning(request, f"⚠️ Beginning inventory already exists for {product.generic_name_dosage} at {branch.branch_name}.", extra_tags="warning")
                else:
                    temp_beginning_inventory_list.append({
                        "product_code": product.product_code,
                        "product_name": str(product.generic_name_dosage),
                        "brand_name": str(product.brand_name.brand_name) if product.brand_name else "",
                        "branch_id": branch.id,
                        "branch_name": branch.branch_name,
                        "fixed_beginning_inventory": fixed_beginning_inventory,
                        "batch_number": batch_number,
                    })
                    request.session["TEMP_BEGINNING_INVENTORY_LIST"] = temp_beginning_inventory_list
                    messages.success(request, "✅ Item added to the temporary beginning inventory list.")

            else:
                messages.error(request, "❌ Invalid data. Please check the form.")

        elif "remove_item" in request.POST:
            product_code = request.POST.get("product_code")
            branch_id = request.POST.get("branch")
            batch_number = request.POST.get("batch_number")

            temp_beginning_inventory_list = [
                item for item in temp_beginning_inventory_list
                if not (item["product_code"] == product_code and
                        item["branch_id"] == int(branch_id) and
                        item["batch_number"] == batch_number)
            ]
            request.session["TEMP_BEGINNING_INVENTORY_LIST"] = temp_beginning_inventory_list
            messages.success(request, "🗑️ Item removed from the temporary list.")

        elif "submit_inventory" in request.POST:
            if not temp_beginning_inventory_list:
                messages.error(request, "⚠️ No items in the list to submit.")
            else:
                for item in temp_beginning_inventory_list:
                    try:
                        product = Product.objects.filter(
                            product_code=item["product_code"],
                            batch__batch_number=item["batch_number"]
                        ).first()

                        if not product:
                            messages.error(request, f"❌ Product {item['product_name']} (Batch {item['batch_number']}) not found.")
                            continue

                        branch = Branch.objects.get(id=item["branch_id"])

                        stock, created = Stock.objects.get_or_create(product=product, branch=branch)

                        if stock.fixed_beginning_inventory > 0:
                            messages.warning(request, f"⚠️ Beginning inventory already exists for {item['product_name']} at {branch.branch_name}.", extra_tags="warning")
                            continue

                        # Update both fixed_beginning_inventory and beginning_inventory
                        stock.fixed_beginning_inventory = item["fixed_beginning_inventory"]
                        stock.beginning_inventory = item["fixed_beginning_inventory"]
                        stock.save()

                        # Log the transaction
                        InventoryTransaction.objects.create(
                            product=product,
                            branch=branch,
                            quantity=item["fixed_beginning_inventory"],
                            transaction_type="Add Beginning Inventory",
                            transaction_date=now(),
                            worker=request.user.worker_profile
                        )

                        messages.success(request, f"✅ Beginning inventory added for {item['product_name']} at {branch.branch_name}.")

                    except Branch.DoesNotExist:
                        messages.error(request, f"❌ Branch with ID {item['branch_id']} not found.")
                    except Exception as e:
                        messages.error(request, f"❌ An error occurred: {e}")

                request.session.pop("TEMP_BEGINNING_INVENTORY_LIST", None)
                return redirect("stock")

    view_context = {
        "form": form,
        "temp_stock": temp_beginning_inventory_list,
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'AddInventoryStock.html', context)



@csrf_exempt
def edit_beginning_inventory(request, stock_id):
    if request.method == "POST":
        try:
            # Parse the incoming JSON body
            data = json.loads(request.body)
            new_inventory = data.get("beginning_inventory")

            # Fetch the stock object
            stock = get_object_or_404(Stock, id=stock_id)
            stock.beginning_inventory = new_inventory  # Update the inventory
            stock.save()

            # Ensure user is authenticated before accessing worker_profile
            if not request.user.is_authenticated:
                return JsonResponse({"success": False, "error": "User not authenticated"})

            # Ensure worker profile exists
            if not hasattr(request.user, 'worker_profile'):
                return JsonResponse({"success": False, "error": "Worker profile not found"})

            # Log the transaction
            InventoryTransaction.objects.create(
                product=stock.product,
                branch=stock.branch,
                quantity=new_inventory,
                transaction_type="Update Beginning Inventory",
                transaction_date=now(),
                worker=request.user.worker_profile,
            )

            # Set a success message
            messages.success(request, "Beginning inventory updated successfully.")
            return JsonResponse({"success": True})

        except Exception as e:
            print(f"Error updating inventory: {e}")  # Log error to console for debugging
            messages.error(request, f"Error updating inventory: {str(e)}")
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request"})




@login_required
def update_stock_view(request):
    form = StockUpdateForm()
    temp_stock_list = request.session.get("TEMP_UPDATE_STOCK_LIST", [])

    if request.method == "POST":
        if "add_to_list" in request.POST:
            form = StockUpdateForm(request.POST)
            if form.is_valid():
                product = form.cleaned_data["product"]
                new_quantity = form.cleaned_data["quantity"]
                branch = form.cleaned_data["branch"]
                batch = form.cleaned_data["batch"]  # Get batch from form
                batch_number = batch.batch_number if batch else None

                try:
                    # Ensure a stock record exists for the given product, branch, and batch
                    stock_entry = Stock.objects.filter(product=product, branch=branch, batch=batch).first()
                except Stock.DoesNotExist:
                    messages.error(request, _(f"No stock record found for {product.generic_name_dosage} (Batch: {batch_number}) in the selected branch."))
                else:
                    # Check if the product, branch, and batch are already in the temporary update list
                    existing_item = next(
                        (item for item in temp_stock_list
                         if item["product_code"] == product.product_code
                         and item["branch_id"] == branch.id
                         and item["batch_number"] == batch_number),
                        None
                    )
                    if existing_item:
                        # Update the quantity in the temporary list (add to existing)
                        existing_item["new_quantity"] += new_quantity
                        messages.success(request, _("Quantity updated in the update list."))
                    else:
                        # Add the item to the temporary update list
                        temp_stock_list.append({
                            "product_code": product.product_code,
                            "product_name": str(product.generic_name_dosage),
                            "brand_name": str(product.brand_name.brand_name if product.brand_name else "No Brand"),
                            "current_quantity": stock_entry.quantity,
                            "new_quantity": new_quantity,
                            "branch_id": branch.id,
                            "branch_name": branch.branch_name,
                            "batch_number": batch_number,
                        })
                        messages.success(request, _(f"Stock added to the update list for {product.generic_name_dosage} (Batch: {batch_number})."))

                    request.session["TEMP_UPDATE_STOCK_LIST"] = temp_stock_list
            else:
                messages.error(request, _("Please correct the errors in the form."))

        elif "remove_item" in request.POST:
            product_code = request.POST.get("product_code")
            branch_id = int(request.POST.get("branch"))
            batch_number = request.POST.get("batch_number")

            # Remove the matching item from the temporary list by product, branch, and batch
            temp_stock_list = [
                item for item in temp_stock_list
                if not (
                    item["product_code"] == product_code
                    and item["branch_id"] == branch_id
                    and item["batch_number"] == batch_number
                )
            ]
            request.session["TEMP_UPDATE_STOCK_LIST"] = temp_stock_list
            messages.success(request, _("Item removed from the update list."))

        elif "update_stock" in request.POST:
            if not temp_stock_list:
                messages.error(request, _("No items in the update list."))
            else:
                for item in temp_stock_list:
                    # Retrieve the correct product and batch
                    product = Product.objects.filter(product_code=item["product_code"]).first()
                    batch = Batch.objects.get(batch_number=item["batch_number"]) if item["batch_number"] else None
                    branch = Branch.objects.get(id=item["branch_id"])

                    # Fetch and update the existing stock record by product, branch, and batch
                    stock = Stock.objects.filter(product=product, branch=branch, batch=batch).first()
                    if not stock:
                        messages.error(request, _(f"No stock record found for {product.generic_name_dosage} (Batch: {item['batch_number']}) in branch {branch.branch_name}."))
                        continue

                    previous_quantity = stock.quantity
                    stock.quantity += item["new_quantity"]
                    stock.total_stock = (stock.begining_inventory or 0) + stock.quantity
                    stock.save()

                    InventoryTransaction.objects.create(
                        product=product,
                        branch=branch,
                        quantity=item["new_quantity"],
                        transaction_type="update",
                        transaction_date=now(),
                        worker=request.user.worker_profile
                    )

                    messages.info(request, _(f"Stock updated for {product.generic_name_dosage} (Batch: {item['batch_number']})."))

                # Clear the temporary update list
                request.session.pop("TEMP_UPDATE_STOCK_LIST", None)
                messages.success(request, _("Stock updated successfully."))
                return redirect("stock")

    view_context = {
        "form": form,
        "temp_stock": temp_stock_list,
    }
    context = TemplateLayout.init(request, view_context)
    return render(request, "updateStock.html", context)




@login_required
def delete_stock_api(request):
    if request.method == "POST":
        data = json.loads(request.body)
        stock_id = data.get("stock_id")
        password = data.get("password")

        # Verify user's password
        user = authenticate(username=request.user.username, password=password)
        if not user:
            return JsonResponse({"success": False, "error": "Invalid password."}, status=400)

        # Find and delete stock
        try:
            stock = Stock.objects.get(id=stock_id)
            stock.delete()
            messages.success(request, "Stock deleted successfully.")
            return JsonResponse({"success": True, "redirect_url": reverse("stocks")})
        except Stock.DoesNotExist:
            return JsonResponse({"success": False, "error": "Stock not found."}, status=404)

    return JsonResponse({"success": False, "error": "Invalid request method."}, status=405)


@login_required
def delete_stock_page(request, stock_id):
    # Fetch the stock object or return a 404 if not found
    stock = get_object_or_404(Stock, id=stock_id)

    if request.method == "POST":
        password = request.POST.get("password")

        # Verify the user's password
        user = authenticate(username=request.user.username, password=password)
        if not user:
            messages.error(request, "Invalid password. Please try again.")
        else:
            # Capture the product and branch before deletion
            product = stock.product
            branch = stock.branch
            quantity = stock.quantity  # Track the quantity being removed
            product_code = product.product_code  # Get the product code for the success message

            # Delete the stock
            stock.delete()

            # Create a transaction record for the deletion
            InventoryTransaction.objects.create(
                product=product,
                branch=branch,
                quantity=-quantity,  # Negative quantity to signify stock removal
                transaction_type="REMOVE",
                transaction_date=now(),
                worker=request.user.worker_profile  # Ensure worker tracking is included
            )

            # Add a success message
            messages.success(request, f"Stock '{product_code}' deleted successfully.")
            return redirect(reverse("stock"))  # Redirect to the stocks page

    # Prepare the context for rendering the template
    view_context = {"stock": stock}
    context = TemplateLayout.init(request, view_context)

    return render(request, "delete_stock.html", context)

@login_required
def update_existing_stock_view(request):

    global TEMP_UPDATE_LIST
    form = StockUpdateForm()  # Initialize form without binding data

    if request.method == "POST":
        if "add_to_list" in request.POST:  # Add stock to temporary list
            product_id = request.POST.get("product")
            branch_id = request.POST.get("branch")
            quantity = request.POST.get("quantity", "").strip()

            if product_id and branch_id:
                product = get_object_or_404(Product, id=product_id)
                branch = get_object_or_404(Branch, id=branch_id)

                # Ensure quantity is valid
                try:
                    quantity = int(quantity)
                    if quantity <= 0:
                        raise ValueError(_("Quantity must be greater than zero."))
                except ValueError:
                    messages.error(request, _("Invalid quantity. Please enter a number greater than zero."))
                    return redirect(request.path)

                # Check if the stock item already exists in the temporary list
                existing_item = next(
                    (item for item in TEMP_UPDATE_LIST
                     if item["product_id"] == product.id and item["branch_id"] == branch.id),
                    None
                )

                if existing_item:
                    messages.warning(request, f"Stock for {product.generic_name_dosage} at {branch.branch_name} is already in the update list.")
                else:
                    TEMP_UPDATE_LIST.append({
                        "product_id": product.id,
                        "product_code": product.product_code,
                        "product_name": product.generic_name_dosage,
                        "brand_name": product.brand_name.brand_name,
                        "quantity": quantity,
                        "branch_id": branch.id,
                        "branch_name": branch.branch_name,
                    })
                    messages.success(request, f"Stock for {product.generic_name_dosage} added to the update list.")
            else:
                messages.error(request, _("Please select a valid product and branch."))

            return redirect(request.path)

        # elif "remove_item" in request.POST:  # Remove stock from the temporary list
        #     product_id = request.POST.get("product_code")
        #     branch_id = request.POST.get("branch")

        #     TEMP_UPDATE_LIST = [
        #         item for item in TEMP_UPDATE_LIST
        #         if not (item["product_id"] == int(product_id) and item["branch_id"] == int(branch_id))
        #     ]
        #     messages.success(request, "Item removed from the update list.")

        elif "remove_item" in request.POST:  # Handle removing from the temporary list
            product_code = request.POST.get("product_code")
            branch_id = request.POST.get("branch")

            # Remove matching item from the temporary list
            TEMP_UPDATE_LIST = [
                item for item in TEMP_UPDATE_LIST
                if not (item["product_code"] == product_code and item["branch_id"] == int(branch_id))
            ]
            # Store the updated list in session
            # request.session["TEMP_UPDATE_LIST"] = TEMP_UPDATE_LIST
            messages.success(request, _("Item removed from the temporary stock list."))

        elif "update_stock" in request.POST:  # Apply updates to the database
            if not TEMP_UPDATE_LIST:
                messages.error(request, _("No items in the update list to update."))
            else:
                for item in TEMP_UPDATE_LIST:
                    product = get_object_or_404(Product, id=item["product_id"])
                    branch = get_object_or_404(Branch, id=item["branch_id"])

                    # Update existing stock
                    stock = Stock.objects.filter(product=product, branch=branch).first()
                    if stock:
                        # Add the new quantity to the existing quantity
                        stock.quantity += item["quantity"]
                        stock.save()

                        # Log the transaction
                        InventoryTransaction.objects.create(
                            product=product,
                            branch=branch,
                            quantity=item["quantity"],
                            transaction_type="update",
                            transaction_date=now()
                        )

                TEMP_UPDATE_LIST = []  # Clear the temporary list
                messages.success(request, _("Stock updates applied successfully."))
                return redirect("stock")  # Adjust redirect to appropriate URL for your project

    # Prepare context for rendering
    view_context = {
        "form": form,
        "temp_stock": TEMP_UPDATE_LIST,
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, "update_stock_entry.html", context)






@login_required
def update_stock_entry_view(request, stock_id):
    # Get the stock entry by ID
    stock = get_object_or_404(Stock, id=stock_id)
    form = UpdateStockForm(instance=stock)  # Pre-fill the form with the current stock

    if request.method == "POST":
        form = UpdateStockForm(request.POST, instance=stock)
        if form.is_valid():
            form.save()  # Update the stock entry in the database
            # Add a transaction record
            InventoryTransaction.objects.create(
                product=stock.product,
                branch=stock.branch,
                quantity=form.cleaned_data['quantity'],
                transaction_type="update"
            )
            messages.success(request, f"Stock updated successfully for {stock.product.generic_name_dosage}.")
            return redirect("stock")  # Replace with your stock tracking page URL name

    view_context = {
        "form": form,
        "stock": stock,
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, "update_stock_entry.html", context)


@login_required
def get_stock_data(request):
    branch_id = request.GET.get("branch_id")
    get_all = request.GET.get("all", "false").lower() == "true"
    search_query = request.GET.get("search_query", "").strip()

    try:
        if get_all:
            stocks = Stock.objects.select_related(
                'product__batch', 'product__brand_name', 'branch'
            )
        elif branch_id:
            branch = Branch.objects.get(id=branch_id)
            stocks = Stock.objects.filter(branch=branch).select_related(
                'product__batch', 'product__brand_name', 'branch'
            )
        else:
            return JsonResponse({"error": "Branch ID not provided"}, status=400)

        # Apply search query if provided
        if search_query:
            stocks = stocks.filter(
                Q(product__product_code__icontains=search_query) |
                Q(product__generic_name_dosage__icontains=search_query) |
                Q(product__brand_name__brand_name__icontains=search_query) |
                Q(product__batch__batch_number__icontains=search_query)
            )

        stocks = stocks.order_by("product__product_code", "product__batch__batch_number")

        stock_data = [
            {
                "id": stock.id,
                "product_code": stock.product.product_code,
                "batch_batch_number": stock.product.batch.batch_number,
                "branch_id": stock.branch.id,
                "branch_name": stock.branch.branch_name,
                "product_name": str(stock.product.generic_name_dosage),
                "brand_name": stock.product.brand_name.brand_name if stock.product.brand_name else "N/A",
                "quantity": stock.quantity,
                "total_inventory": stock.total_inventory,
                "begining_inventory": stock.begining_inventory,
                "fixed_beginning_inventory": stock.fixed_beginning_inventory,
                "total_stock": stock.total_stock,
                "total_sold": stock.total_sold,
                "quantity_transferred": stock.quantity_transferred,
            }
            for stock in stocks
        ]

        return JsonResponse({
            "branch_name": branch.branch_name if branch_id else "All Branches",
            "stocks": stock_data
        })

    except Branch.DoesNotExist:
        return JsonResponse({"error": "Branch not found"}, status=404)









@login_required
def get_branches(request):
    branches = Branch.objects.all()
    branch_data = [
        {"id": branch.id, "name": branch.branch_name}
        for branch in branches
    ]
    return JsonResponse({"branches": branch_data})

@login_required
def track_stocks(request):
    # Get all branches for the filter dropdown
    branches = Branch.objects.all()

    # Get filter and search query from request
    branch_filter = request.GET.get('branch_filter', '').strip()
    search_query = request.GET.get('search_query', '').strip()

    # Fetch stock data with related models for efficiency
    all_stocks = Stock.objects.select_related('product', 'product__generic_name_dosage', 'branch')

    # Apply branch filter
    if branch_filter:
        all_stocks = all_stocks.filter(branch_id=branch_filter)

    # Apply search filter
    if search_query:
        all_stocks = all_stocks.filter(
            Q(product__product_code__icontains=search_query) |
            Q(product__generic_name_dosage__generic_name__icontains=search_query)| # Correct lookup
            Q(product__brand_name__brand_name__icontains=search_query)| # Correct lookup
            Q(product__batch__batch_number__icontains=search_query)
        )

    # Paginate results
    paginator = Paginator(all_stocks, 100)
    page_number = request.GET.get('page')
    paginated_stocks = paginator.get_page(page_number)
    offset = (paginated_stocks.number - 1) * paginator.per_page

    # Get all products for Select2 dropdown
    all_products = Product.objects.all()

    # Prepare context
    view_context = {
        "stocks": paginated_stocks,
        "branches": branches,
        "search_query": search_query,
        "branch_filter": branch_filter,
        "all_products": all_products,
        "offset": offset,
    }

    context = TemplateLayout.init(request, view_context)

    return render(request, "stock_all.html", context)
