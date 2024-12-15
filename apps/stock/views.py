from django.views.generic import TemplateView
from web_project import TemplateLayout
from .forms import StockUpdateForm, UpdateStockForm
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from apps.products.models import Product
from apps.branches.models import Branch
from .models import Stock, InventoryTransaction
from django.utils.timezone import now  # To handle timestamps
from django.http import JsonResponse
from apps.workers.models import Worker
from django.contrib.auth.decorators import login_required

"""
This file is a view controller for multiple pages as a module.
Here you can override the page view layout.
Refer to tables/urls.py file for more pages.
"""

# Temp storage for demonstration; use sessions or database in production
TEMP_STOCK_LIST = []  
TEMP_UPDATE_LIST = []  # Temporary list for selected stocks


def ManageStockView(request):
    stocks = Stock.objects.all()

    # Create a new context dictionary for this view 
    view_context = {
        "stocks": stocks,
    }

    # Initialize the template layout and merge the view context
    context = TemplateLayout.init(request, view_context)

    return render(request, 'stock.html', context)

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



def add_stock_view(request):
    form = StockUpdateForm()

    # Retrieve temporary stock list from session or create an empty list
    temp_stock_list = request.session.get("TEMP_STOCK_LIST", [])

    if request.method == "POST":
        if "add_to_list" in request.POST:  # Handle adding to the temporary list
            form = StockUpdateForm(request.POST)
            if form.is_valid():
                product = form.cleaned_data["product"]
                quantity = form.cleaned_data["quantity"]
                branch = form.cleaned_data["branch"]

                # Add item to temporary list
                temp_stock_list.append({
                    "product_code": product.product_code,
                    "product_name": product.generic_name_dosage,
                    "quantity": quantity,
                    "branch_id": branch.id,
                    "branch_name": branch.branch_name,
                })
                # Store the updated temporary list in session
                request.session["TEMP_STOCK_LIST"] = temp_stock_list
                messages.success(request, "Item added to temporary stock list.")
            else:
                messages.error(request, "Invalid data. Please check the form.")

        elif "remove_item" in request.POST:  # Handle removing from the temporary list
            product_code = request.POST.get("product_code")
            branch_id = request.POST.get("branch")

            # Remove matching item from the temporary list
            temp_stock_list = [
                item for item in temp_stock_list 
                if not (item["product_code"] == product_code and item["branch_id"] == int(branch_id))
            ]
            # Store the updated list in session
            request.session["TEMP_STOCK_LIST"] = temp_stock_list
            messages.success(request, "Item removed from the temporary stock list.")

        elif "update_stock" in request.POST:  # Handle updating stock in the database
            for item in temp_stock_list:
                product = Product.objects.get(product_code=item["product_code"])
                branch = Branch.objects.get(id=item["branch_id"])

                # Update or create stock entry
                stock, created = Stock.objects.update_or_create(
                    product=product,
                    branch=branch,
                    defaults={"quantity": item["quantity"]}
                )

                # Create a transaction record
                transaction_type = 'add' if created else 'update'
                InventoryTransaction.objects.create(
                    product=product,
                    branch=branch,
                    quantity=item["quantity"],
                    transaction_type=transaction_type,
                    transaction_date=now()
                )

                if created:
                    messages.info(request, f"Stock added for product {product.generic_name_dosage}.")
                else:
                    messages.info(request, f"Stock updated for product {product.generic_name_dosage}.")

            # Clear the temporary list
            del request.session["TEMP_STOCK_LIST"]
            messages.success(request, "Stock updated successfully.")
            return redirect("stock")  # Replace with the correct URL name

    # Prepare context for rendering
    view_context = {
        "form": form,
        "temp_stock": temp_stock_list,
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'AddStock.html', context)



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
                        raise ValueError("Quantity must be greater than zero.")
                except ValueError:
                    messages.error(request, "Invalid quantity. Please enter a number greater than zero.")
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
                        "quantity": quantity,
                        "branch_id": branch.id,
                        "branch_name": branch.branch_name,
                    })
                    messages.success(request, f"Stock for {product.generic_name_dosage} added to the update list.")
            else:
                messages.error(request, "Please select a valid product and branch.")

            return redirect(request.path)

        elif "remove_item" in request.POST:  # Remove stock from the temporary list
            product_id = request.POST.get("product_id")
            branch_id = request.POST.get("branch_id")

            TEMP_UPDATE_LIST = [
                item for item in TEMP_UPDATE_LIST
                if not (item["product_id"] == int(product_id) and item["branch_id"] == int(branch_id))
            ]
            messages.success(request, "Item removed from the update list.")

        elif "update_stock" in request.POST:  # Apply updates to the database
            if not TEMP_UPDATE_LIST:
                messages.error(request, "No items in the update list to update.")
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
                messages.success(request, "Stock updates applied successfully.")
                return redirect("stock")  # Adjust redirect to appropriate URL for your project

    # Prepare context for rendering
    view_context = {
        "form": form,
        "temp_stock": TEMP_UPDATE_LIST,
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, "UpdateStock.html", context)







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



def get_stock_data(request):
    branch_id = request.GET.get('branch_id')

    if not branch_id:
        return JsonResponse({"error": "Branch ID not provided"}, status=400)

    try:
        branch = Branch.objects.get(id=branch_id)
        stocks = Stock.objects.filter(branch=branch)
        stock_data = [
            {
                "id": stock.id,
                "product_code": stock.product.product_code,
                "branch_id": stock.branch.branch_id,
                "branch_name": stock.branch.branch_name,
                "product_name": str(stock.product.generic_name_dosage),  # Ensure this is a string
                "quantity": stock.quantity,
            }
            for stock in stocks
        ]
        return JsonResponse({"branch_name": branch.branch_name, "stocks": stock_data})
    except Branch.DoesNotExist:
        return JsonResponse({"error": "Branch not found"}, status=404)

    


def get_branches(request):
    branches = Branch.objects.all()
    branch_data = [
        {"id": branch.id, "name": branch.branch_name}
        for branch in branches
    ]
    return JsonResponse({"branches": branch_data})
