from django.urls import path
from .views import ManageRecommedationView, add_recommend_view



urlpatterns = [
    path(
        "recommendations/",
        ManageRecommedationView,
        name="recommend",
    ),
    path(
        "new-recommendations/",
        add_recommend_view,
        name="new-recommend",
    ),
    
]
