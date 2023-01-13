from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from model_utils.base.admin import BaseModelAdmin
from .models import Address, Country, Locality, State, Timezone


@admin.register(Address)
class AddressModelAdmin(BaseModelAdmin):
    fieldsets = (
        (
            _('base information'),
            {
                'fields': (
                    'locality',
                    'street_address',
                    'apartment_name',
                    'native_street_address',
                    'native_apartment_name',
                ),
            },
        ),
        (
            _('geographic information'),
            {'fields': ('latitude', 'longitude')},
        ),
    )
    list_display = ('__str__', 'locality__state__country')
    list_select_related = ('locality', 'locality__state', 'locality__state__country')
    ordering = (
        'locality__state__country__name',
        'locality__state__name',
        'locality__name',
        'street_address',
        'native_street_address',
    )
    search_fields = (
        'street_address',
        'apartment_name',
        'native_street_address',
        'native_apartment_name',
        'locality__name',
        'locality__native_name',
        'locality__state__name',
        'locality__state__native_name',
        'locality__state__country__name',
        'locality__state__country__native_name',
    )

    @admin.display(description=_('country'))
    def locality__state__country(self, obj):
        return obj.locality.state.country


@admin.register(Country)
class CountryModelAdmin(BaseModelAdmin):
    fieldsets = (
        (
            _('base information'),
            {
                'fields': (
                    'name',
                    'native_name',
                    'emoji',
                    'calling_code',
                    'iso2_code',
                    'iso3_code',
                    'numeric_code',
                ),
            },
        ),
        (
            _('geographic information'),
            {'fields': ('region', 'subregion', 'capital_name', 'tld')},
        ),
        (
            _('currency'),
            {'fields': ('currency_name', 'currency_code', 'currency_symbol')},
        ),
    )
    list_display = ('__str__', 'emoji')
    list_filter = ('region',)
    ordering = ('name',)
    search_fields = ('name', 'native_name')


@admin.register(Locality)
class LocalityModelAdmin(BaseModelAdmin):
    fields = (
        'state',
        'name',
        'native_name',
        'postal_code',
    )
    list_display = ('__str__', 'state__country')
    list_filter = ('state__country',)
    list_select_related = ('state', 'state__country')
    ordering = ('state__country__name', 'state__name', 'name', 'native_name')
    search_fields = (
        'name',
        'native_name',
        'postal_code',
        'state__name',
        'state__country__name',
        'state__country__native_name',
    )

    @admin.display(description=_('country'))
    def state__country(self, obj):
        return obj.state.country


@admin.register(State)
class StateModelAdmin(BaseModelAdmin):
    fields = (
        'country',
        'name',
        'native_name',
        'code',
        'type',
    )
    list_display = ('__str__', 'country')
    list_filter = ('country',)
    list_select_related = ('country',)
    ordering = ('country', 'name')
    search_fields = (
        'name',
        'native_name',
        'code',
        'country__name',
        'country__native_name',
    )


@admin.register(Timezone)
class TimezoneModelAdmin(BaseModelAdmin):
    fields = (
        'country',
        'name',
        'code',
        'abbreviation',
        'utc_offset_name',
        'utc_offset',
    )
    list_display = ('__str__', 'country', 'abbreviation', 'utc_offset_name')
    list_filter = ('country',)
    list_select_related = ('country',)
    ordering = ('code', 'abbreviation')
    search_fields = (
        'name',
        'code',
        'abbreviation',
        'country__name',
        'country__native_name',
    )
