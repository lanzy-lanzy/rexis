from django.urls import path
from . import views

urlpatterns = [
    path('', views.proposal_list, name='proposal_list'),
    path('create/', views.proposal_create, name='proposal_create'),
    path('<int:pk>/', views.proposal_detail, name='proposal_detail'),
    path('<int:pk>/edit/', views.proposal_edit, name='proposal_edit'),
    path('<int:pk>/review/', views.proposal_review, name='proposal_review'),
    path('htmx/list/', views.proposal_htmx_list, name='proposal_htmx_list'),
    path('validate/', views.validate_proposal, name='proposal_validate'),
]
