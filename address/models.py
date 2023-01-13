from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from model_utils.base.models import BaseModel


class Address(BaseModel):
    apartment_name = models.CharField(
        _('apartment name'),
        max_length=128,
        blank=True,
        default='',
    )
    latitude = models.DecimalField(
        _('latitude'),
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        default=None,
    )
    locality = models.ForeignKey(
        'address.Locality',
        on_delete=models.PROTECT,
        verbose_name=_('locality'),
    )
    longitude = models.DecimalField(
        _('longitude'),
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        default=None,
    )
    native_apartment_name = models.CharField(
        _('apartment name in native language'),
        max_length=128,
        blank=True,
        default='',
    )
    native_street_address = models.CharField(
        _('street address in native language'),
        max_length=128,
        blank=True,
        default='',
    )
    street_address = models.CharField(
        _('street address'),
        max_length=128,
        blank=True,
        default='',
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    ~models.Q(street_address__exact='')
                    | ~models.Q(native_street_address__exact='')
                ),
                name='required_street_address_or_native_street_address',
            ),
        ]
        ordering = (
            'locality__state__country__name',
            'locality__state__name',
            'locality__name',
            'street_address',
            'native_street_address',
        )
        verbose_name = _('address')
        verbose_name_plural = _('addresses')

    def __str__(self):
        return (
            self.native_full_address
            or self.full_address
            or self.native_sub_address
            or self.sub_address
        )

    @property
    def sub_address(self):
        if self.street_address:
            if self.apartment_name:
                return _('{first_address}, {second_address}').format(
                    first_address=self.apartment_name,
                    second_address=self.street_address,
                )

            return self.street_address

        return ''

    @property
    def native_sub_address(self):
        if self.native_street_address:
            if self.native_apartment_name:
                return _('{first_address}, {second_address}').format(
                    first_address=self.native_apartment_name,
                    second_address=self.native_street_address,
                )

            return self.native_street_address

        return ''

    @property
    def full_address(self):
        if self.locality.full_locality_name:
            if self.sub_address:
                return _('{first_address}, {second_address}').format(
                    first_address=self.sub_address,
                    second_address=self.locality.full_locality_name,
                )

        return ''

    @property
    def native_full_address(self):
        if self.locality.native_full_locality_name:
            if self.native_sub_address:
                return _('{first_address}, {second_address}').format(
                    first_address=self.native_sub_address,
                    second_address=self.locality.native_full_locality_name,
                )

        return ''


class Country(BaseModel):
    calling_code = models.CharField(
        _('calling code'),
        max_length=32,
        blank=True,
        default='',
    )
    capital_name = models.CharField(
        _('capital name'),
        max_length=64,
        blank=True,
        default='',
    )
    currency_code = models.CharField(
        _('currency code'),
        max_length=3,
        blank=True,
        default='',
        validators=[RegexValidator(r'^[A-Z]{3}\Z')],
    )
    currency_name = models.CharField(
        _('currency name'),
        max_length=64,
        blank=True,
        default='',
    )
    currency_symbol = models.CharField(
        _('currency symbol'),
        max_length=16,
        blank=True,
        default='',
    )
    emoji = models.CharField(
        _('emoji'),
        max_length=2,
        blank=True,
        default='',
        validators=[
            RegexValidator(
                r'['
                u'\U0001F600-\U0001F64F'
                u'\U0001F300-\U0001F5FF'
                u'\U0001F680-\U0001F6FF'
                u'\U0001F1E0-\U0001F1FF'
                u'\U00002500-\U00002BEF'
                u'\U00002702-\U000027B0'
                u'\U00002702-\U000027B0'
                u'\U000024C2-\U0001F251'
                u'\U0001f926-\U0001f937'
                u'\U00010000-\U0010ffff'
                u'\u2640-\u2642'
                u'\u2600-\u2B55'
                u'\u200d'
                u'\u23cf'
                u'\u23e9'
                u'\u231a'
                u'\ufe0f'
                u'\u3030'
                ']+'
            ),
        ],
    )
    iso2_code = models.CharField(
        _('country code (ISO 3166-1 alpha-2)'),
        max_length=2,
        blank=True,
        default='',
        validators=[RegexValidator(r'^[A-Z]{2}\Z')],
    )
    iso3_code = models.CharField(
        _('country code (ISO 3166-1 alpha-3)'),
        max_length=3,
        blank=True,
        default='',
        validators=[RegexValidator(r'^[A-Z]{3}\Z')],
    )
    name = models.CharField(_('country name'), max_length=64, unique=True)
    native_name = models.CharField(
        _('country name in native language'),
        max_length=64,
        blank=True,
        default='',
    )
    numeric_code = models.CharField(
        _('numeric code (ISO 3166-1 numeric)'),
        max_length=3,
        blank=True,
        default='',
        validators=[RegexValidator(r'^[0-9]{3}\Z')],
    )
    region = models.CharField(_('region name'), max_length=16, blank=True, default='')
    subregion = models.CharField(
        _('subregion name'),
        max_length=32,
        blank=True,
        default='',
    )
    tld = models.CharField(
        _('ccTLD (country code top-level domain)'),
        max_length=2,
        blank=True,
        default='',
        validators=[RegexValidator(r'^.[a-z]{2}\Z')],
    )

    class Meta:
        ordering = ('name',)
        verbose_name = _('country')
        verbose_name_plural = _('countries')

    def __str__(self):
        return self.native_name or self.name


class Locality(BaseModel):
    name = models.CharField(
        _('locality name'),
        max_length=128,
        blank=True,
        default='',
    )
    native_name = models.CharField(
        _('locality name in native language'),
        max_length=128,
        blank=True,
        default='',
    )
    postal_code = models.CharField(
        _('postal code'),
        max_length=16,
        blank=True,
        default='',
    )
    state = models.ForeignKey(
        'address.State',
        on_delete=models.PROTECT,
        verbose_name=_('state'),
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=~models.Q(name__exact='') | ~models.Q(native_name__exact=''),
                name='required_name_or_native_name',
            ),
        ]
        ordering = ('state__country__name', 'state__name', 'name', 'native_name')
        verbose_name = _('locality')
        verbose_name_plural = _('localities')

    def __str__(self):
        return (
            self.native_full_locality_name
            or self.full_locality_name
            or self.native_name
            or self.name
        )

    @property
    def full_locality_name(self):
        if self.name:
            if self.postal_code:
                return _('{locality_name}, {state_name} {postal_code}').format(
                    state_name=self.state.name,
                    locality_name=self.name,
                    postal_code=self.postal_code,
                )

            return _('{locality_name}, {state_name}').format(
                state_name=self.state.name,
                locality_name=self.name,
            )

        return ''

    @property
    def native_full_locality_name(self):
        if self.state.native_name:
            if self.native_name:
                if self.postal_code:
                    return _('{locality_name}, {state_name} {postal_code}').format(
                        state_name=self.state.native_name,
                        locality_name=self.native_name,
                        postal_code=self.postal_code,
                    )

                return _('{locality_name}, {state_name}').format(
                    state_name=self.state.native_name,
                    locality_name=self.native_name,
                )

        return ''


class State(BaseModel):
    code = models.CharField(_('code'), max_length=8, blank=True, default='')
    country = models.ForeignKey(
        'address.Country',
        on_delete=models.PROTECT,
        verbose_name=_('country'),
    )
    name = models.CharField(_('state name'), max_length=64)
    native_name = models.CharField(
        _('state name in native language'),
        max_length=64,
        blank=True,
        default='',
    )
    type = models.CharField(_('type'), max_length=64, blank=True, default='')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['country', 'name', 'code'],
                name='unique_country_and_state_name_and_code',
            ),
        ]
        ordering = ('country', 'name')
        verbose_name = _('state')
        verbose_name_plural = _('states')

    def __str__(self):
        return self.native_name or self.name


class Timezone(BaseModel):
    abbreviation = models.CharField(
        _('abbreviation'),
        max_length=8,
        blank=True,
        default='',
    )
    code = models.CharField(_('code'), max_length=64)
    country = models.ForeignKey(
        'address.Country',
        on_delete=models.PROTECT,
        verbose_name=_('country'),
    )
    utc_offset = models.IntegerField(
        _('utc offset (sec)'),
        blank=True,
        null=True,
        default=None,
    )
    utc_offset_name = models.CharField(
        _('utc offset name'),
        max_length=16,
        blank=True,
        default='',
        validators=[RegexValidator(r'^UTC[±+-]\d\d(:\d\d)?\Z')],
    )
    name = models.CharField(_('timezone name'), max_length=64)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['country', 'code'],
                name='unique_country_and_timezone_code',
            ),
        ]
        ordering = ('code', 'abbreviation')
        verbose_name = _('timezone')
        verbose_name_plural = _('timezones')

    def __str__(self):
        return self.code
