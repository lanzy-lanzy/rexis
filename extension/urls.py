from django.urls import path
from . import views

urlpatterns = [
    path('', views.extension_list, name='extension_list'),
    path('create/', views.extension_create, name='extension_create'),
    path('<int:pk>/', views.extension_detail, name='extension_detail'),
    path('<int:pk>/edit/', views.extension_edit, name='extension_edit'),
]
