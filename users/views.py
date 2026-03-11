from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.utils.decorators import method_decorator

from .models import CustomUser, UserRole
from .forms import CustomUserCreationForm, CustomUserChangeForm, FrontendUserChangeForm


def login_view(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'registration/login.html')


def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    return redirect('login')


@login_required
def user_management(request: HttpRequest) -> HttpResponse:
    if not request.user.is_admin:
        messages.error(request, 'Access denied. Admin only.')
        return redirect('dashboard')
    
    users = CustomUser.objects.all().order_by('-date_joined')
    return render(request, 'users/user_management.html', {'users': users})


@login_required
def user_create(request: HttpRequest) -> HttpResponse:
    if not request.user.is_admin:
        messages.error(request, 'Access denied. Admin only.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = form.cleaned_data['role']
            user.save()
            messages.success(request, f'User {user.username} created successfully.')
            return redirect('user_management')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/user_form.html', {'form': form})


@login_required
def user_edit(request: HttpRequest, pk: int) -> HttpResponse:
    if not request.user.is_admin:
        messages.error(request, 'Access denied. Admin only.')
        return redirect('dashboard')
    
    user = get_object_or_404(CustomUser, pk=pk)
    if request.method == 'POST':
        form = FrontendUserChangeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'User {user.username} updated successfully.')
            return redirect('user_management')
    else:
        form = FrontendUserChangeForm(instance=user)
    return render(request, 'users/user_form.html', {'form': form, 'user_obj': user})


@login_required
def user_delete(request: HttpRequest, pk: int) -> HttpResponse:
    if not request.user.is_admin:
        messages.error(request, 'Access denied. Admin only.')
        return redirect('dashboard')
    
    user = get_object_or_404(CustomUser, pk=pk)
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User {username} deleted successfully.')
        return redirect('user_management')
    return render(request, 'users/user_confirm_delete.html', {'user': user})
