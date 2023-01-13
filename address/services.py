from typing import Optional
from uuid import UUID

from address.models import Address, Country, Locality, State
from django.db.models.query import QuerySet
from django.db.utils import IntegrityError


class AddressService:
    _address_model = Address
    _country_model = Country
    _locality_model = Locality
    _state_model = State

    def get_country_set(self: 'AddressService') -> QuerySet[Country]:
        queryset = self._country_model.objects.all()
        queryset = queryset.filter(deleted_at__isnull=True)
        queryset = queryset.prefetch_related(
            'state_set',
            'timezone_set',
            'state__locality_set',
            'state__locality__address_set',
        )
        return queryset

    def get_country(
        self: 'AddressService',
        *,
        id: Optional[str] = None,
    ) -> Optional[Country]:
        if not isinstance(id, str):
            raise ValueError

        queryset = self._country_model.objects.all()
        queryset = queryset.filter(id=UUID(id))  # raise: ValueError
        queryset = queryset.filter(deleted_at__isnull=True)
        queryset = queryset.prefetch_related(
            'state_set',
            'timezone_set',
            'state__locality_set',
            'state__locality__address_set',
        )

        try:
            return queryset.get()

        except self._country_model.DoesNotExist:
            return None

    def get_state_set(
        self: 'AddressService',
        *,
        country: Optional[Country] = None,
    ) -> QuerySet[State]:
        if not isinstance(country, Country):
            raise ValueError

        queryset: QuerySet[State] = country.state_set.all()
        queryset = queryset.filter(deleted_at__isnull=True)
        queryset = queryset.select_related('country')
        queryset = queryset.prefetch_related('locality_set', 'locality__address_set')
        return queryset

    def get_state(
        self: 'AddressService',
        *,
        id: Optional[str] = None,
    ) -> Optional[State]:
        if not isinstance(id, str):
            raise ValueError

        queryset = self._state_model.objects.all()
        queryset = queryset.filter(id=UUID(id))  # raise: ValueError
        queryset = queryset.filter(deleted_at__isnull=True)
        queryset = queryset.select_related('country')
        queryset = queryset.prefetch_related('locality_set', 'locality__address_set')

        try:
            return queryset.get()

        except self._state_model.DoesNotExist:
            return None

    def get_is_state_exists(
        self: 'AddressService',
        *,
        id: Optional[str] = None,
    ) -> bool:
        if not isinstance(id, str):
            raise ValueError

        queryset = self._state_model.objects.all()
        queryset = queryset.filter(id=UUID(id))  # raise: ValueError
        queryset = queryset.filter(deleted_at__isnull=True)
        return queryset.exists()

    def get_locality_set(
        self: 'AddressService',
        *,
        state: Optional[State] = None,
    ) -> QuerySet[Locality]:
        if not isinstance(state, State):
            raise ValueError

        queryset: QuerySet[Locality] = state.locality_set.all()
        queryset = queryset.filter(deleted_at__isnull=True)
        queryset = queryset.select_related('state', 'state__country')
        queryset = queryset.prefetch_related('address_set')
        return queryset

    def get_locality(
        self: 'AddressService',
        *,
        id: Optional[str] = None,
    ) -> Optional[Locality]:
        if not isinstance(id, str):
            raise ValueError

        queryset = self._locality_model.objects.all()
        queryset = queryset.filter(id=UUID(id))  # raise: ValueError
        queryset = queryset.filter(deleted_at__isnull=True)
        queryset = queryset.select_related('state', 'state__country')
        queryset = queryset.prefetch_related('address_set')

        try:
            return queryset.get()

        except self._locality_model.DoesNotExist:
            return None

    def get_is_locality_exists(
        self: 'AddressService',
        *,
        id: Optional[str] = None,
    ) -> bool:
        if not isinstance(id, str):
            raise ValueError

        queryset = self._locality_model.objects.all()
        queryset = queryset.filter(id=UUID(id))  # raise: ValueError
        queryset = queryset.filter(deleted_at__isnull=True)
        return queryset.exists()

    def create_locality(
        self: 'AddressService',
        *,
        state_id: Optional[str] = None,
        name: Optional[str] = None,
        native_name: Optional[str] = None,
        postal_code: Optional[str] = None,
    ) -> Locality:
        if not self.get_is_state_exists(id=state_id):
            raise ValueError

        kwargs = {'state_id': UUID(state_id)}
        kwargs.update({'name': name} if name is not None else {})
        kwargs.update({'native_name': native_name} if native_name is not None else {})
        kwargs.update({'postal_code': postal_code} if postal_code is not None else {})

        try:
            return self._locality_model.objects.create(**kwargs)

        except IntegrityError as e:
            raise ValueError from e

    def update_locality(
        self: 'AddressService',
        *,
        locality: Optional[Locality] = None,
        state_id: Optional[str] = None,
        name: Optional[str] = None,
        native_name: Optional[str] = None,
        postal_code: Optional[str] = None,
    ) -> Locality:
        if locality is not None:
            raise ValueError

        is_updated = False

        if state_id is not None:
            if not self.get_is_state_exists(id=state_id):
                raise ValueError

            locality.state_id = state_id
            is_updated = True

        if name is not None:
            locality.name = name
            is_updated = True

        if native_name is not None:
            locality.native_name = native_name
            is_updated = True

        if postal_code is not None:
            locality.postal_code = postal_code
            is_updated = True

        if is_updated:
            locality.save()

        return locality

    def get_address_set(self: 'AddressService') -> QuerySet[Address]:
        queryset = self._address_model.objects.all()
        queryset = queryset.filter(deleted_at__isnull=True)
        queryset = queryset.select_related(
            'locality',
            'locality__state',
            'locality__state__country',
        )
        return queryset

    def get_address(
        self: 'AddressService',
        *,
        id: Optional[str] = None,
    ) -> Optional[Address]:
        if not isinstance(id, str):
            raise ValueError

        queryset = self._address_model.objects.all()
        queryset = queryset.filter(id=UUID(id))  # raise: ValueError
        queryset = queryset.filter(deleted_at__isnull=True)
        queryset = queryset.select_related(
            'locality',
            'locality__state',
            'locality__state__country',
        )

        try:
            return queryset.get()

        except self._address_model.DoesNotExist:
            return None

    def create_address(
        self: 'AddressService',
        *,
        state_id: Optional[str] = None,
        locality_id: Optional[str] = None,
        apartment_name: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        native_apartment_name: Optional[str] = None,
        native_street_address: Optional[str] = None,
        street_address: Optional[str] = None,
        locality_name: Optional[str] = None,
        locality_native_name: Optional[str] = None,
        locality_postal_code: Optional[str] = None,
    ) -> Address:
        if locality_id:
            if (
                state_id is not None
                or locality_name is not None
                or locality_native_name is not None
                or locality_postal_code is not None
            ):
                raise ValueError

        else:
            if self.get_is_state_exists(id=state_id):
                locality = self.create_locality(
                    state_id=state_id,
                    name=locality_name,
                    native_name=locality_native_name,
                    postal_code=locality_postal_code,
                )
                locality_id = locality.id

        if not self.get_is_locality_exists(id=locality_id):
            raise ValueError

        try:
            return self._address_model.objects.create(
                locality_id=UUID(locality_id),
                apartment_name=apartment_name,
                latitude=latitude,
                longitude=longitude,
                native_apartment_name=native_apartment_name,
                native_street_address=native_street_address,
                street_address=street_address,
            )

        except IntegrityError as e:
            raise ValueError from e

    def update_address(
        self: 'AddressService',
        *,
        address: Optional[Address] = None,
        state_id: Optional[str] = None,
        locality_id: Optional[str] = None,
        apartment_name: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        native_apartment_name: Optional[str] = None,
        native_street_address: Optional[str] = None,
        street_address: Optional[str] = None,
        locality_name: Optional[str] = None,
        locality_native_name: Optional[str] = None,
        locality_postal_code: Optional[str] = None,
        create_new_locality: bool = False,
    ) -> Address:
        if locality_id:
            address.locality = self.get_locality(id=locality_id)

            if not address.locality:
                raise ValueError

        if (
            state_id is not None
            or locality_name is not None
            or locality_native_name is not None
            or locality_postal_code is not None
        ):
            if create_new_locality and not locality_id:
                address.locality = self.create_locality(
                    state_id=state_id,
                    name=locality_name,
                    native_name=locality_native_name,
                    postal_code=locality_postal_code,
                )

                if not address.locality:
                    raise ValueError

            else:
                self.update_locality(
                    locality=address.locality,
                    state_id=state_id,
                    name=locality_name,
                    native_name=locality_native_name,
                    postal_code=locality_postal_code,
                )

        if apartment_name is not None:
            address.apartment_name = apartment_name

        if latitude is not None:
            address.latitude = latitude

        if longitude is not None:
            address.longitude = longitude

        if native_apartment_name is not None:
            address.native_apartment_name = native_apartment_name

        if native_street_address is not None:
            address.native_street_address = native_street_address

        if street_address is not None:
            address.street_address = street_address

        address.save()

        return address
