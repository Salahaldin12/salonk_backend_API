
from django.urls import path 
from . import views 

urlpatterns = [
    path('store/', views.get_all_products),
    path('store/<str:pk>/', views.get_by_id_product),
    path('categories/', views.CategoryListView.as_view()),

]
