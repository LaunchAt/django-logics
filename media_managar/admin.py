from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from model_utils.base.admin import BaseModelAdmin
from .models import Media


@admin.register(Media)
class MediaModelAdmin(BaseModelAdmin):
    fieldsets = (
        ('', {'fields': ('title',)}),
        (_('external media'), {'fields': ('external_url',)}),
        (_('file'), {'fields': ('file', 'file_location', 'file_name')}),
    )
    list_display = ('title', 'url')
    ordering = ('-created_at',)
    search_fields = (
        'external_url',
        'file',
        'file_location',
        'file_name',
        'id',
        'title',
    )

    @admin.display(description=_('url'))
    def url(self, obj):
        return obj.url
