from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from model_utils.base.admin import BaseModelAdmin
from .models import MediaFile


@admin.register(MediaFile)
class MediaFileModelAdmin(BaseModelAdmin):
    fieldsets = (
        (_('base information'), {'fields': ('title', 'owner')}),
        (_('external file'), {'fields': ('external_url',)}),
        (_('uploaded file'), {'fields': ('file', 'file_location', 'file_name')}),
    )
    list_display = ('title', 'url', 'owner')
    ordering = ('-created_at',)
    search_fields = (
        'external_url',
        'file',
        'file_location',
        'file_name',
        'id',
        'title',
        'owner__id',
    )

    @admin.display(description=_('url'))
    def url(self, obj):
        return obj.url
