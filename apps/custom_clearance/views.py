from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import ClearanceStep, ClearanceProcess, ClearanceProcessGroup, CustomLogs
from .forms import ClearanceProcessForm, ClearanceProcessGroupForm, ClearanceStepForm
from web_project import TemplateLayout
from django.core.paginator import Paginator


@login_required
def add_clearance_process(request):
    """View to add a new clearance process for the user."""
    if request.method == "POST":
        # Create a new ClearanceProcessGroup instance
        form = ClearanceProcessGroupForm(request.POST, request.FILES)
        if form.is_valid():
            process_group = form.save(commit=False)
            process_group.user = request.user  # Assign the logged-in user
            process_group.save()

            # Log the creation of the process
            CustomLogs.objects.create(
                user=request.user,
                action="PROCESS_CREATED",
                description=f"User started a new clearance process (ID: {process_group.id})."
            )

            # Automatically start the first step of the process
            first_step = ClearanceStep.objects.first()  # Get the first predefined step
            if first_step:
                # Make sure to handle the cost field
                cost = 0.00  # Set default value if required
                ClearanceProcess.objects.create(
                    user=request.user,
                    process_group=process_group,
                    step=first_step,
                    completed=False,
                    cost=cost  # Add the cost value here
                )
                CustomLogs.objects.create(
                    user=request.user,
                    action="STEP_STARTED",
                    description=f"User started the first step: {first_step.name} (Step ID: {first_step.id}) in Process Group {process_group.id}."
                )

            messages.success(request, "New clearance process started successfully!")
            return redirect('clearance_dashboard')  # Redirect to the clearance dashboard
    else:
        form = ClearanceProcessGroupForm()

    view_context = {'form': form}

    context = TemplateLayout.init(request, view_context)
    return render(request, "addClearanceProcess.html", context)






@login_required
def clearance_dashboard(request):
    """View to track clearance progress, allow step creation, and edit process details."""
    process_id = request.GET.get('process_id')
    edit_process_id = request.GET.get('edit_process_id')  # Get the process_id for editing from URL params

    # Fetch the specific clearance process group
    if process_id:
        process_group = ClearanceProcessGroup.objects.filter(id=process_id).first()
    else:
        process_group = ClearanceProcessGroup.objects.order_by('-created_at').first()

    if not process_group:
        CustomLogs.objects.create(
            user=request.user,
            action="REDIRECTED",
            description="User redirected to start a new clearance process (no active session)."
        )
        return redirect('start_clearance_process')

    # Fetch all predefined steps
    steps = ClearanceStep.objects.all().order_by("step_number")

    # Fetch completed steps
    completed_steps = ClearanceProcess.objects.filter(process_group=process_group, completed=True)
    completed_step_ids = completed_steps.values_list('step_id', flat=True)

    # Determine the next step
    next_step = None
    for step in steps:
        if step.id not in completed_step_ids:
            next_step = step
            break

    # If editing a process, populate the form with existing data
    if edit_process_id:
        process_instance = get_object_or_404(ClearanceProcess, id=edit_process_id)
        form = ClearanceProcessForm(request.POST or None, request.FILES or None, instance=process_instance)
        is_editing = True
    else:
        form = ClearanceProcessForm(request.POST or None, request.FILES or None)
        is_editing = False

    if request.method == "POST":
        if 'submit_process' in request.POST:  # Handle process completion or editing
            if form.is_valid():
                if is_editing:
                    # Update the existing process
                    form.save()
                    CustomLogs.objects.create(
                        user=request.user,
                        action="PROCESS_UPDATED",
                        description=f"User updated process for step {form.instance.step.name} (Process ID: {form.instance.id})."
                    )
                    messages.success(request, "Process updated successfully!")
                else:
                    # Create a new process
                    form.instance.user = request.user
                    form.instance.process_group = process_group
                    form.instance.step = next_step
                    form.instance.completed = True
                    form.save()
                    CustomLogs.objects.create(
                        user=request.user,
                        action="STEP_COMPLETED",
                        description=f"User completed step {next_step.name} (Step ID: {next_step.id}) in Process Group {process_group.id}."
                    )
                    messages.success(request, f"Step {next_step.name} completed successfully!")
                return redirect('clearance_dashboard')

    # Calculate progress percentage
    total_steps = steps.count()
    completed_steps_count = completed_steps.count()
    progress_percentage = (completed_steps_count / total_steps * 100) if total_steps > 0 else 0

    view_context = {
        "steps": steps,
        "completed_steps": completed_steps,
        "completed_step_ids": completed_step_ids,
        "next_step": next_step,
        "form": form,
        "process_group": process_group,
        "progress_percentage": progress_percentage,
        "is_editing": is_editing,
    }

    context = TemplateLayout.init(request, view_context)

    return render(request, "custom_dashboard.html", context)



@login_required
def edit_clearance_step(request, step_id):
    """View to edit clearance step details."""
    step = get_object_or_404(ClearanceStep, id=step_id)  # Fetch the step or return 404 if not found

    if request.method == "POST":
        form = ClearanceStepForm(request.POST, instance=step)  # Bind the form to the step instance
        if form.is_valid():
            updated_step = form.save()
            CustomLogs.objects.create(
                user=request.user,
                action="STEP_EDITED",
                description=f"User edited clearance step {updated_step.name} (Step ID: {updated_step.id})."
            )
            messages.success(request, "Step details updated successfully!")
            return redirect("clearance_dashboard")  # Redirect to dashboard or another relevant page
    else:
        form = ClearanceStepForm(instance=step)  # Populate the form with existing step data

    context = TemplateLayout.init(request, {"form": form, "step": step, "is_editing": True,})
    return render(request, "custom_dashboard.html", context)





@login_required
def start_clearance_process(request):
    """Starts a new customs clearance process while keeping old ones."""
    new_process_group = ClearanceProcessGroup.objects.create(user=request.user)
    CustomLogs.objects.create(
        user=request.user,
        action="SESSION_START",
        description=f"User started a new clearance process (Process Group ID: {new_process_group.id})."
    )
    messages.success(request, "New clearance process started!")
    return redirect('clearance_dashboard')


@login_required
def clearance_history(request):
    """View all past customs clearance processes."""
    process_groups = ClearanceProcessGroup.objects.order_by('-created_at')

    view_context = {"process_groups": process_groups}

    context = TemplateLayout.init(request, view_context)

    return render(request, "clearance_history.html", context)


@login_required
def view_custom_logs(request):
    """View to display user logs for customs clearance actions with pagination."""
    logs_list = CustomLogs.objects.filter(user=request.user).order_by('-created_at')

    # Pagination setup: Show 10 logs per page
    paginator = Paginator(logs_list, 10)
    page_number = request.GET.get('page')
    logs = paginator.get_page(page_number)

    view_context = {"logs": logs}
    context = TemplateLayout.init(request, view_context)

    return render(request, "custom_logs.html", context)
