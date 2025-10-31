# Additional Proforma Views - To be merged into views.py

@login_required
def create_proforma(request):
    """Create a new proforma"""
    if request.user.is_superuser:
        user_is_superuser = True
        user_branch = None
    else:
        user_is_superuser = False
        user_branch = request.user.worker_profile.branch

    if request.method == 'POST':
        form = ProformaForm(request.POST, user_is_superuser=user_is_superuser, user_branch=user_branch)
        if form.is_valid():
            created_at = form.cleaned_data["created_at"]
            created_at_str = created_at.strftime('%Y-%m-%d %H:%M:%S')

            # Save form data to session (similar to purchase order flow)
            request.session["proforma_details"] = {
                "created_at": created_at_str,
                "branch": form.cleaned_data["branch"].id if user_is_superuser else user_branch.id,
                "customer": form.cleaned_data["customer"].id,
                "sales_rep": form.cleaned_data["sales_rep"].id if form.cleaned_data["sales_rep"] else None,
                "payment_method": form.cleaned_data["payment_method"],
                "payment_mode": form.cleaned_data["payment_mode"],
                "momo_account_details": form.cleaned_data["momo_account_details"].id if form.cleaned_data.get("momo_account_details") else None,
                "check_account_details": form.cleaned_data["check_account_details"].id if form.cleaned_data.get("check_account_details") else None,
                "bank_deposit_account_details": form.cleaned_data["bank_deposit_account_details"].id if form.cleaned_data.get("bank_deposit_account_details") else None,
                "tax_rate": str(form.cleaned_data["tax_rate"]),
                "precompte": str(form.cleaned_data["precompte"]),
                "tva": str(form.cleaned_data["tva"]),
                "is_special_customer": form.cleaned_data["is_special_customer"],
                "notes": form.cleaned_data.get("notes", ""),
            }

            # Redirect to add items page
            return redirect("add_proforma_items")
        else:
            messages.error(request, _("Invalid form submission. Please correct the errors."))
    else:
        form = ProformaForm(user_is_superuser=user_is_superuser, user_branch=user_branch)

    view_context = {'form': form}
    context = TemplateLayout.init(request, view_context)
    return render(request, 'createProforma.html', context)


@login_required
def add_proforma_items(request):
    """Add items to a proforma (similar to add_order_items)"""
    user_branch = request.user.worker_profile.branch

    # Retrieve proforma details from session
    proforma_details = request.session.get("proforma_details", {})
    if not proforma_details:
        messages.error(request, _("Please create a proforma first."))
        return redirect("create_proforma")

    selected_branch_id = proforma_details.get("branch")
    selected_branch = get_object_or_404(Branch, id=selected_branch_id) if selected_branch_id else user_branch

    # Initialize session data if it doesn't exist
    if "proforma_items" not in request.session:
        request.session["proforma_items"] = []

    item_form = ProformaItemForm(user_branch=selected_branch)
    stocks = Stock.objects.select_related('product').filter(branch=selected_branch)

    if request.method == "POST":
        if "add_item" in request.POST:
            item_form = ProformaItemForm(request.POST, user_branch=selected_branch)
            if item_form.is_valid():
                stock = item_form.cleaned_data["stock"]
                quantity = item_form.cleaned_data["quantity"]
                temp_price = item_form.cleaned_data.get("temp_price")
                reason = item_form.cleaned_data.get("reason", "")

                # Add item to session
                item_data = {
                    "stock_id": stock.id,
                    "quantity": quantity,
                    "temp_price": str(temp_price) if temp_price else None,
                    "reason": reason,
                }
                request.session["proforma_items"].append(item_data)
                request.session.modified = True
                messages.success(request, _("Item added successfully."))
                return redirect("add_proforma_items")

        elif "remove_item" in request.POST:
            item_index = int(request.POST.get("remove_item"))
            if 0 <= item_index < len(request.session["proforma_items"]):
                request.session["proforma_items"].pop(item_index)
                request.session.modified = True
                messages.success(request, _("Item removed successfully."))
            return redirect("add_proforma_items")

        elif "save_proforma" in request.POST:
            # Create the proforma with items
            if not request.session.get("proforma_items"):
                messages.error(request, _("Please add at least one item to the proforma."))
                return redirect("add_proforma_items")

            try:
                with transaction.atomic():
                    # Get proforma details from session
                    proforma_details = request.session.get("proforma_details", {})

                    # Create proforma
                    proforma = Proforma.objects.create(
                        created_at=datetime.strptime(proforma_details["created_at"], '%Y-%m-%d %H:%M:%S'),
                        branch_id=proforma_details["branch"],
                        customer_id=proforma_details["customer"],
                        sales_rep_id=proforma_details.get("sales_rep"),
                        payment_method=proforma_details["payment_method"],
                        payment_mode=proforma_details.get("payment_mode"),
                        momo_account_id=proforma_details.get("momo_account_details"),
                        check_account_id=proforma_details.get("check_account_details"),
                        bank_deposit_account_id=proforma_details.get("bank_deposit_account_details"),
                        tax_rate=Decimal(proforma_details["tax_rate"]),
                        precompte=Decimal(proforma_details["precompte"]),
                        tva=Decimal(proforma_details["tva"]),
                        is_special_customer=proforma_details.get("is_special_customer", False),
                        notes=proforma_details.get("notes", ""),
                        created_by=request.user.worker_profile,
                    )

                    # Calculate grand total
                    grand_total = Decimal('0.00')

                    # Add items
                    for item_data in request.session["proforma_items"]:
                        stock = Stock.objects.get(id=item_data["stock_id"])
                        quantity = int(item_data["quantity"])
                        temp_price = Decimal(item_data["temp_price"]) if item_data.get("temp_price") else None

                        price = temp_price if temp_price else stock.product.unit_price
                        item_total = price * quantity
                        grand_total += item_total

                        ProformaItem.objects.create(
                            proforma=proforma,
                            stock=stock,
                            quantity=quantity,
                            temp_price=temp_price,
                            reason=item_data.get("reason", ""),
                        )

                    # Update grand total
                    proforma.grand_total = grand_total
                    proforma.save()

                    # Log action
                    log_proforma_action(request.user, proforma, "create", f"Proforma created with {len(request.session['proforma_items'])} items")

                    # Clear session
                    request.session.pop("proforma_details", None)
                    request.session.pop("proforma_items", None)

                    messages.success(request, _("Proforma created successfully!"))
                    return redirect("proforma_details", proforma_id=proforma.id)

            except Exception as e:
                messages.error(request, _(f"Error creating proforma: {str(e)}"))
                return redirect("add_proforma_items")

    # Build items list for display
    items_list = []
    for item_data in request.session.get("proforma_items", []):
        try:
            stock = Stock.objects.get(id=item_data["stock_id"])
            temp_price = Decimal(item_data["temp_price"]) if item_data.get("temp_price") else None
            price = temp_price if temp_price else stock.product.unit_price
            quantity = int(item_data["quantity"])

            items_list.append({
                "stock": stock,
                "quantity": quantity,
                "price": price,
                "total": price * quantity,
                "reason": item_data.get("reason", ""),
            })
        except Stock.DoesNotExist:
            continue

    view_context = {
        "item_form": item_form,
        "stocks": stocks,
        "items_list": items_list,
        "proforma_details": proforma_details,
    }

    context = TemplateLayout.init(request, view_context)
    return render(request, "addProformaItems.html", context)


@login_required
def proforma_details(request, proforma_id):
    """View proforma details"""
    proforma = get_object_or_404(Proforma, id=proforma_id)
    items = proforma.items.all()

    # Calculate totals
    subtotal = sum(item.get_total_price() for item in items)
    tax_amount = (subtotal * proforma.tax_rate) / Decimal('100') if proforma.tax_rate else Decimal('0')
    tva_amount = (subtotal * proforma.tva) / Decimal('100') if proforma.tva else Decimal('0')
    precompte_amount = (subtotal * proforma.precompte) / Decimal('100') if proforma.precompte else Decimal('0')

    if proforma.is_special_customer:
        total_with_taxes = (subtotal + tva_amount + precompte_amount) - tax_amount
    else:
        total_with_taxes = (subtotal + tva_amount + precompte_amount) - tax_amount

    view_context = {
        "proforma": proforma,
        "items": items,
        "subtotal": subtotal,
        "tax_amount": tax_amount,
        "tva_amount": tva_amount,
        "precompte_amount": precompte_amount,
        "total_with_taxes": total_with_taxes,
    }

    context = TemplateLayout.init(request, view_context)
    return render(request, "proformaDetails.html", context)


@login_required
def edit_proforma(request, proforma_id):
    """Edit an existing proforma"""
    proforma = get_object_or_404(Proforma, id=proforma_id)

    if proforma.is_promoted:
        messages.error(request, _("Cannot edit a proforma that has been promoted to an order."))
        return redirect("proforma_details", proforma_id=proforma.id)

    if request.user.is_superuser:
        user_is_superuser = True
        user_branch = None
    else:
        user_is_superuser = False
        user_branch = request.user.worker_profile.branch

    if request.method == 'POST':
        form = ProformaForm(request.POST, instance=proforma, user_is_superuser=user_is_superuser, user_branch=user_branch)
        if form.is_valid():
            # Update payment accounts
            proforma.momo_account = form.cleaned_data.get("momo_account_details")
            proforma.check_account = form.cleaned_data.get("check_account_details")
            proforma.bank_deposit_account = form.cleaned_data.get("bank_deposit_account_details")

            form.save()

            log_proforma_action(request.user, proforma, "update", "Proforma details updated")
            messages.success(request, _("Proforma updated successfully!"))
            return redirect("proforma_details", proforma_id=proforma.id)
    else:
        form = ProformaForm(instance=proforma, user_is_superuser=user_is_superuser, user_branch=user_branch)
        # Set initial values for payment accounts
        form.fields['momo_account_details'].initial = proforma.momo_account
        form.fields['check_account_details'].initial = proforma.check_account
        form.fields['bank_deposit_account_details'].initial = proforma.bank_deposit_account

    view_context = {
        'form': form,
        'proforma': proforma,
    }

    context = TemplateLayout.init(request, view_context)
    return render(request, 'editProforma.html', context)


@login_required
def promote_proforma_to_order(request, proforma_id):
    """Promote a proforma to an actual purchase order"""
    proforma = get_object_or_404(Proforma, id=proforma_id)

    if proforma.is_promoted:
        messages.error(request, _("This proforma has already been promoted to an order."))
        return redirect("proforma_details", proforma_id=proforma.id)

    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Create PurchaseOrder from Proforma
                purchase_order = PurchaseOrder.objects.create(
                    order_type='Purchase Order',
                    created_at=proforma.created_at,
                    branch=proforma.branch,
                    customer=proforma.customer,
                    sales_rep=proforma.sales_rep,
                    payment_method=proforma.payment_method,
                    payment_mode=proforma.payment_mode,
                    momo_account=proforma.momo_account,
                    check_account=proforma.check_account,
                    bank_deposit_account=proforma.bank_deposit_account,
                    tax_rate=proforma.tax_rate,
                    precompte=proforma.precompte,
                    tva=proforma.tva,
                    is_special_customer=proforma.is_special_customer,
                    status='Pending',
                    grand_total=proforma.grand_total,
                    created_by=request.user.worker_profile,
                )

                # Copy items
                for proforma_item in proforma.items.all():
                    PurchaseOrderItem.objects.create(
                        purchase_order=purchase_order,
                        stock=proforma_item.stock,
                        quantity=proforma_item.quantity,
                        temp_price=proforma_item.temp_price,
                        reason=proforma_item.reason,
                    )

                # Mark proforma as promoted
                proforma.is_promoted = True
                proforma.promoted_to_order = purchase_order
                proforma.save()

                # Log actions
                log_proforma_action(request.user, proforma, "promote", f"Promoted to order {purchase_order.purchase_order_id}")

                PurchaseOrderAuditLog.objects.create(
                    user=request.user.worker_profile,
                    order=purchase_order.purchase_order_id,
                    branch=purchase_order.branch.branch_name,
                    action="create",
                    details=f"Created from proforma {proforma.proforma_id}"
                )

                messages.success(request, _("Proforma promoted to order successfully!"))

                # Redirect to payment schedule creation if credit
                if purchase_order.payment_method == 'Credit':
                    return redirect("create_payment_schedule")
                else:
                    return redirect("order_details", order_id=purchase_order.id)

        except Exception as e:
            messages.error(request, _(f"Error promoting proforma: {str(e)}"))
            return redirect("proforma_details", proforma_id=proforma.id)

    view_context = {
        'proforma': proforma,
    }

    context = TemplateLayout.init(request, view_context)
    return render(request, 'promoteProforma.html', context)


@login_required
def delete_proforma(request, proforma_id):
    """Delete a proforma"""
    proforma = get_object_or_404(Proforma, id=proforma_id)

    if proforma.is_promoted:
        messages.error(request, _("Cannot delete a proforma that has been promoted to an order."))
        return redirect("proforma_details", proforma_id=proforma.id)

    if request.method == 'POST':
        proforma_id_str = proforma.proforma_id
        proforma.delete()
        log_proforma_action(request.user, None, "delete", f"Deleted proforma {proforma_id_str}")
        messages.success(request, _("Proforma deleted successfully!"))
        return redirect("proformas")

    view_context = {
        'proforma': proforma,
    }

    context = TemplateLayout.init(request, view_context)
    return render(request, 'deleteProforma.html', context)
