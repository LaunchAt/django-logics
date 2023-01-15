import os

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from model_utils.base.models import BaseModel

USER_MODEL = getattr(settings, 'MEDIAFILE_USER_MODEL', settings.AUTH_USER_MODEL)


class MediaFile(BaseModel):
    def get_upload_to(self, filename):
        location = self.file_location

        if location.endswith('/'):
            location = location[:-1]

        name = self.file_name or self.id
        extension = os.path.splitext(filename)[-1]
        return '{}/{}.{}'.format(location, name, extension)

    title = models.CharField(
        _('title'),
        max_length=32,
        blank=True,
        default='',
    )
    external_url = models.URLField(_('external url'), blank=True, default='')
    file_location = models.CharField(
        _('file location'),
        max_length=128,
        blank=True,
        default='',
    )
    file_name = models.CharField(_('file name'), max_length=64, blank=True, default='')
    file = models.FileField(_('file'), upload_to=get_upload_to, blank=True, default='')
    owner = models.ForeignKey(
        USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name=_('owner'),
        blank=True,
        null=True,
        default=None,
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    Q(external_url='') & ~Q(file='') | ~Q(external_url='') & Q(file='')
                ),
                name='not_both_external_url_and_file_blank',
            ),
        ]
        ordering = ('-created_at',)
        verbose_name = _('media file')
        verbose_name_plural = _('media file')

    def __str__(self):
        return self.title

    @property
    def url(self):
        return self.external_url or self.file.url
