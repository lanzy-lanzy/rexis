from django.urls import path
from . import views

urlpatterns = [
    path('', views.extension_list, name='extension_list'),
    path('create/', views.extension_create, name='extension_create'),
    path('<int:pk>/', views.extension_detail, name='extension_detail'),
    path('<int:pk>/edit/', views.extension_edit, name='extension_edit'),
    path('<int:pk>/reports/add/', views.add_narrative_report, name='add_extension_report'),
    path('reports/quarterly/', views.quarterly_reports_list, name='quarterly_reports'),
]
