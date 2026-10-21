from django.contrib.auth.models import User
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class LostFoundItem(models.Model):
    STATUS_CHOICES = [
        ('LOST', 'Lost'),
        ('FOUND', 'Found'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, null=True, blank=True
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    location = models.CharField(max_length=200)
    image = models.ImageField(upload_to='item_images/', blank=True, null=True)
    date_reported = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-date_reported']

    def __str__(self):
        return self.title


class StudentProfile(models.Model):
    PURPOSE_CHOICES = [
        ('searching', 'Finding a lost item / searching'),
        ('reporting', 'Reporting found items'),
        ('both', 'Both searching and reporting'),
    ]
    CATEGORY_CHOICES = [
        ('electronics', 'Electronics and laptops'),
        ('IDs', 'Student IDs and cards'),
        ('books', 'Books and course materials'),
        ('keys', 'Keys and wallets'),
        ('clothing', 'Clothing and accessories'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    phone_number = models.CharField(max_length=30, blank=True)
    register_purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES, default='both')
    search_category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, blank=True)
    emergency_contact_name = models.CharField(max_length=150, blank=True)
    emergency_contact_phone = models.CharField(max_length=30, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)

    def __str__(self):
        return f'{self.user.username} profile'
