from django.contrib.auth.models import AbstractUser
from django.db import models


class UserRole(models.TextChoices):
    ADMIN = 'ADMIN', 'Administrator'
    FACULTY = 'FACULTY', 'Faculty'
    RESEARCH_STAFF = 'RESEARCH_STAFF', 'Research Staff'
    EXTENSION_STAFF = 'EXTENSION_STAFF', 'Extension Staff'


class CustomUser(AbstractUser):
    ROLE_CHOICES = UserRole.choices
    
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.FACULTY
    )
    employee_id = models.CharField(max_length=50, blank=True)
    department = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN or self.is_superuser

    @property
    def is_faculty(self):
        return self.role == UserRole.FACULTY

    @property
    def is_research_staff(self):
        return self.role == UserRole.RESEARCH_STAFF

    @property
    def is_extension_staff(self):
        return self.role == UserRole.EXTENSION_STAFF
