from django.views.generic import TemplateView
from web_project import TemplateLayout
from django.shortcuts import get_object_or_404, render, redirect
from .models import BrandNameModel
from .forms import BrandForm

# Create your views here.
def ManageBrandView(request):
    brandName = BrandNameModel.objects.all()

    # Create a new context dictionary for this view 
    view_context = {
        "brandName": brandName,
    }

    # Initialize the template layout and merge the view context
    context = TemplateLayout.init(request, view_context)

    return render(request, 'add_brandName.html', context)


def add_brand_view(request):
    
    brandName = BrandNameModel.objects.all()
    
    if request.method == "POST":
        form = BrandForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('add-brandName')
    else:
        form = BrandForm()
    view_context = {
        "form": form,
        "brandName": brandName,
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'add_brandName.html', context)

def edit_brand_view(request, pk):
    brand = get_object_or_404(BrandNameModel, pk=pk)  
    
    if request.method == "POST":
        form = BrandForm(request.POST, instance=brand)  
        if form.is_valid():
            form.save()
            return redirect('add-brandName')  
    else:
        form = BrandForm(instance=brand)  

    brand = BrandNameModel.objects.all()  

    view_context = {
        "form": form,
        "brand": brand,
        "is_editing": True,  
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'add_brandName.html', context)