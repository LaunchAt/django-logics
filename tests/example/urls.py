from django.contrib import admin
from django.urls import path
from django.utils.translation import gettext_lazy as _

urlpatterns = [path('', admin.site.urls)]
