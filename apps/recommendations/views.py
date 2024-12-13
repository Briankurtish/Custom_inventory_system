from django.views.generic import TemplateView
from web_project import TemplateLayout
from django.shortcuts import get_object_or_404, render, redirect
from .models import Recommendation
from .forms import RecommendationForm


"""
This file is a view controller for multiple pages as a module.
Here you can override the page view layout.
Refer to tables/urls.py file for more pages.
"""


def ManageRecommedationView(request):
    recommendation = Recommendation.objects.all()

    # Create a new context dictionary for this view 
    view_context = {
        "recommendation": recommendation,
    }

    # Initialize the template layout and merge the view context
    context = TemplateLayout.init(request, view_context)

    return render(request, 'recommend.html', context)


def add_recommend_view(request, pk=None):
    if pk:
        recommend = get_object_or_404(Recommendation, pk=pk)
        form = RecommendationForm(request.POST or None, request.FILES or None, instance=recommend)
    else:
        form = RecommendationForm(request.POST or None, request.FILES or None)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            return redirect('recommend')  # Redirect to the list page after saving

    view_context = {
        "form": form,
        "is_editing": bool(pk),  # Indicates if we are editing
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'newRecommend.html', context)
