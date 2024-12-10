from django.urls import path
from .views import recommendationView



urlpatterns = [
    path(
        "recommendations/",
        recommendationView.as_view(template_name="recommend.html"),
        name="recommend",
    ),
    path(
        "new-recommendations/",
        recommendationView.as_view(template_name="newRecommend.html"),
        name="new-recommend",
    ),
    
]
