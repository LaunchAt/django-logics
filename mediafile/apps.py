from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MediafileConfig(AppConfig):
    name = 'mediafile'
    verbose_name = _('media file')
