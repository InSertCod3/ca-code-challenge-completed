from django.urls import path
from reviews import views

urlpatterns = [
    path("", views.home, name="home"),
    path("brand/", views.brand_index, name="brand_index"),
    path("brand/<slug:slug>/", views.brand_detail, name="brand_detail"),
    path("review/<slug:slug>/", views.review_detail, name="review_detail"),
    path("api/brands/", views.brand_list_api, name="api_brands"),
    path("api/brands/<slug:slug>/", views.brand_detail_api, name="api_brand_detail"),
    path("api/reviews/recent/", views.recent_reviews_api, name="api_recent_reviews"),
    path("api/reviews/<slug:slug>/", views.review_detail_api, name="api_review_detail"),
]
